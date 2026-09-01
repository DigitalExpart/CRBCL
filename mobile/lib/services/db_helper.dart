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
      version: 1,
      onCreate: _createDB,
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

    // Offline Outbox Sync Queue
    await db.execute('''
      CREATE TABLE sync_queue (
        mutation_id TEXT PRIMARY KEY,
        entity_type TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'PENDING'
      )
    ''');
  }

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

  /// Cascade tombstone deletion when server revokes case authorization
  Future<void> purgeCaseCascade(String caseId) async {
    final db = await instance.database;
    await db.transaction((txn) async {
      // Delete main case row
      await txn.delete('cases', where: 'id = ?', whereArgs: [caseId]);
      
      // Delete associated pending sync items referencing this case_id
      await txn.delete('sync_queue', where: 'payload_json LIKE ?', whereArgs: ['%"case_id":"$caseId"%']);
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
