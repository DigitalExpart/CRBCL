import 'dart:convert';
import 'dart:math';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:path/path.dart';
import 'package:sqflite_sqlcipher/sqflite.dart';

class LocalDatabaseHelper {
  static final LocalDatabaseHelper instance = LocalDatabaseHelper._init();
  static Database? _database;
  static const _secureStorage = FlutterSecureStorage();
  static const _dbKeyName = 'crbcl_sqlite_aes_key';

  LocalDatabaseHelper._init();

  Future<Database> get database async {
    if (_database != null) return _database!;
    final password = await _getOrCreateEncryptionKey();
    _database = await _initDB('crbcl_field_encrypted.db', password);
    return _database!;
  }

  Future<String> _getOrCreateEncryptionKey() async {
    String? existingKey = await _secureStorage.read(key: _dbKeyName);
    if (existingKey == null) {
      final random = Random.secure();
      final values = List<int>.generate(32, (i) => random.nextInt(256));
      existingKey = base64Url.encode(values);
      await _secureStorage.write(key: _dbKeyName, value: existingKey);
    }
    return existingKey;
  }

  Future<Database> _initDB(String filePath, String password) async {
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, filePath);

    return await openDatabase(
      path,
      password: password, // SQLCipher AES-256 Encryption
      version: 2,
      onCreate: _createDB,
      onUpgrade: _upgradeDB,
    );
  }

  Future<void> _createDB(Database db, int version) async {
    // Local Cached Cases
    await db.execute('''
      CREATE TABLE cases (
        id TEXT PRIMARY KEY,
        case_number TEXT NOT NULL,
        title TEXT NOT NULL,
        status TEXT NOT NULL,
        stage TEXT NOT NULL,
        updated_at TEXT NOT NULL
      )
    ''');

    // Local Cached Clients
    await db.execute('''
      CREATE TABLE clients (
        id TEXT PRIMARY KEY,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        status TEXT NOT NULL
      )
    ''');

    // Legacy sync queue
    await db.execute('''
      CREATE TABLE sync_queue (
        mutation_id TEXT PRIMARY KEY,
        entity_type TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'PENDING'
      )
    ''');

    // Unified Encrypted Offline Drafts Repository
    await db.execute('''
      CREATE TABLE offline_drafts (
        id TEXT PRIMARY KEY,
        entity_type TEXT NOT NULL,
        title TEXT NOT NULL,
        subtitle TEXT,
        payload_json TEXT NOT NULL,
        sync_status TEXT NOT NULL DEFAULT 'PENDING',
        server_id TEXT,
        person_id_number TEXT,
        referral_number TEXT,
        error_message TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        user_id TEXT
      )
    ''');

    // Server-to-Client Temporary ID Resolution Ledger
    await db.execute('''
      CREATE TABLE id_mappings (
        temp_id TEXT PRIMARY KEY,
        server_id TEXT NOT NULL,
        entity_type TEXT NOT NULL,
        created_at TEXT NOT NULL
      )
    ''');
  }

  Future<void> _upgradeDB(Database db, int oldVersion, int newVersion) async {
    if (oldVersion < 2) {
      await db.execute('''
        CREATE TABLE IF NOT EXISTS offline_drafts (
          id TEXT PRIMARY KEY,
          entity_type TEXT NOT NULL,
          title TEXT NOT NULL,
          subtitle TEXT,
          payload_json TEXT NOT NULL,
          sync_status TEXT NOT NULL DEFAULT 'PENDING',
          server_id TEXT,
          person_id_number TEXT,
          referral_number TEXT,
          error_message TEXT,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          user_id TEXT
        )
      ''');

      await db.execute('''
        CREATE TABLE IF NOT EXISTS id_mappings (
          temp_id TEXT PRIMARY KEY,
          server_id TEXT NOT NULL,
          entity_type TEXT NOT NULL,
          created_at TEXT NOT NULL
        )
      ''');
    }
  }

  // --- Offline Drafts Repository Methods ---

  /// Insert or update an offline draft record
  Future<void> saveDraft({
    required String id,
    required String entityType,
    required String title,
    String? subtitle,
    required Map<String, dynamic> payload,
    String? userId,
  }) async {
    final db = await instance.database;
    final now = DateTime.now().toIso8601String();

    await db.insert(
      'offline_drafts',
      {
        'id': id,
        'entity_type': entityType.toUpperCase(),
        'title': title,
        'subtitle': subtitle,
        'payload_json': jsonEncode(payload),
        'sync_status': 'PENDING',
        'created_at': now,
        'updated_at': now,
        'user_id': userId,
      },
      conflictAlgorithm: ConflictAlgorithm.replace,
    );

    // Also mirror into sync_queue for backwards compatibility
    await db.insert(
      'sync_queue',
      {
        'mutation_id': id,
        'entity_type': entityType.toUpperCase(),
        'payload_json': jsonEncode(payload),
        'created_at': now,
        'status': 'PENDING',
      },
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  /// Update draft sync status and server returned identifiers
  Future<void> updateDraftSyncResult({
    required String id,
    required String status,
    String? serverId,
    String? personIdNumber,
    String? referralNumber,
    String? errorMessage,
  }) async {
    final db = await instance.database;
    final now = DateTime.now().toIso8601String();

    final updates = <String, dynamic>{
      'sync_status': status,
      'updated_at': now,
    };
    if (serverId != null) updates['server_id'] = serverId;
    if (personIdNumber != null) updates['person_id_number'] = personIdNumber;
    if (referralNumber != null) updates['referral_number'] = referralNumber;
    if (errorMessage != null) updates['error_message'] = errorMessage;

    await db.update('offline_drafts', updates, where: 'id = ?', whereArgs: [id]);

    if (status == 'SYNCED') {
      await db.delete('sync_queue', where: 'mutation_id = ?', whereArgs: [id]);
    }
  }

  /// Record server ID mapping for temporary offline UUID
  Future<void> recordIdMapping({
    required String tempId,
    required String serverId,
    required String entityType,
  }) async {
    final db = await instance.database;
    await db.insert(
      'id_mappings',
      {
        'temp_id': tempId,
        'server_id': serverId,
        'entity_type': entityType,
        'created_at': DateTime.now().toIso8601String(),
      },
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  /// Retrieve mapped server ID for a temporary UUID
  Future<String?> getMappedServerId(String tempId) async {
    final db = await instance.database;
    final results = await db.query('id_mappings', columns: ['server_id'], where: 'temp_id = ?', whereArgs: [tempId]);
    if (results.isNotEmpty) {
      return results.first['server_id'] as String?;
    }
    return null;
  }

  /// Get pending drafts that need to be pushed to the server
  Future<List<Map<String, dynamic>>> getPendingDrafts() async {
    final db = await instance.database;
    return await db.query(
      'offline_drafts',
      where: 'sync_status = ? OR sync_status = ?',
      whereArgs: ['PENDING', 'FAILED'],
      orderBy: 'created_at ASC',
    );
  }

  /// Get all drafts, optionally filtered by sync status
  Future<List<Map<String, dynamic>>> getAllDrafts({String? statusFilter}) async {
    final db = await instance.database;
    if (statusFilter != null && statusFilter.isNotEmpty && statusFilter != 'ALL') {
      return await db.query('offline_drafts', where: 'sync_status = ?', whereArgs: [statusFilter], orderBy: 'updated_at DESC');
    }
    return await db.query('offline_drafts', orderBy: 'updated_at DESC');
  }

  /// Delete a local draft
  Future<void> deleteDraft(String id) async {
    final db = await instance.database;
    await db.delete('offline_drafts', where: 'id = ?', whereArgs: [id]);
    await db.delete('sync_queue', where: 'mutation_id = ?', whereArgs: [id]);
  }

  /// Get counts for metrics display
  Future<Map<String, int>> getSyncMetrics() async {
    final db = await instance.database;
    final rows = await db.rawQuery('''
      SELECT sync_status, COUNT(*) as count
      FROM offline_drafts
      GROUP BY sync_status
    ''');

    final metrics = {
      'PENDING': 0,
      'SYNCED': 0,
      'FAILED': 0,
      'NEEDS_REVIEW': 0,
    };

    for (var row in rows) {
      final status = (row['sync_status'] as String?) ?? '';
      final count = (row['count'] as int?) ?? 0;
      if (metrics.containsKey(status)) {
        metrics[status] = count;
      }
    }
    return metrics;
  }

  // --- Legacy Compatibility Methods ---

  Future<int> insertSyncItem(String mutationId, String entityType, String payloadJson) async {
    final db = await instance.database;
    return await db.insert('sync_queue', {
      'mutation_id': mutationId,
      'entity_type': entityType,
      'payload_json': payloadJson,
      'created_at': DateTime.now().toIso8601String(),
      'status': 'PENDING',
    });
  }

  Future<List<Map<String, dynamic>>> getPendingSyncItems() async {
    final db = await instance.database;
    return await db.query('sync_queue', where: 'status = ?', whereArgs: ['PENDING']);
  }

  Future<void> clearSyncedItem(String mutationId) async {
    final db = await instance.database;
    await db.delete('sync_queue', where: 'mutation_id = ?', whereArgs: [mutationId]);
  }

  Future<void> purgeCaseCascade(String caseId) async {
    final db = await instance.database;
    await db.transaction((txn) async {
      await txn.delete('cases', where: 'id = ?', whereArgs: [caseId]);
      await txn.delete('sync_queue', where: 'payload_json LIKE ?', whereArgs: ['%"case_id":"$caseId"%']);
      await txn.delete('offline_drafts', where: 'payload_json LIKE ?', whereArgs: ['%"case_id":"$caseId"%']);
    });
  }

  Future<void> purgeDatabase() async {
    if (_database != null) {
      await _database!.close();
      _database = null;
    }
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, 'crbcl_field_encrypted.db');
    await deleteDatabase(path);
    await _secureStorage.delete(key: _dbKeyName);
  }
}
