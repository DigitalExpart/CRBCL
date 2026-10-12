import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:intl/intl.dart';
import '../services/auth_service.dart';
import '../services/db_helper.dart';
import '../services/sync_engine.dart';
import 'client_draft_screen.dart';
import 'intake_draft_screen.dart';
import 'note_draft_screen.dart';
import 'visit_draft_screen.dart';

class FieldDashboardScreen extends StatefulWidget {
  const FieldDashboardScreen({super.key});

  @override
  State<FieldDashboardScreen> createState() => _FieldDashboardScreenState();
}

class _FieldDashboardScreenState extends State<FieldDashboardScreen> {
  final _dbHelper = LocalDatabaseHelper.instance;
  final _authService = MobileAuthService.instance;

  bool _isLoading = true;
  bool _isSyncing = false;
  bool _isOnline = false;
  DateTime? _lastSyncTime;
  Map<String, int> _metrics = {'PENDING': 0, 'SYNCED': 0, 'FAILED': 0, 'NEEDS_REVIEW': 0};
  List<Map<String, dynamic>> _drafts = [];
  String _activeFilter = 'ALL';
  String _userName = 'Caseworker';

  @override
  void initState() {
    super.initState();
    _loadDashboardData();
  }

  Future<void> _loadDashboardData() async {
    setState(() => _isLoading = true);
    final metrics = await _dbHelper.getSyncMetrics();
    final drafts = await _dbHelper.getAllDrafts(statusFilter: _activeFilter);
    final user = await _authService.getCurrentUser();

    // Check connectivity
    await _checkConnectivityStatus();

    if (mounted) {
      setState(() {
        _metrics = metrics;
        _drafts = drafts;
        _userName = (user['name'] as String?)?.isNotEmpty == true ? user['name'] : 'Caseworker';
        _isLoading = false;
      });
    }
  }

  Future<void> _checkConnectivityStatus() async {
    try {
      final serverUrl = await _authService.getServerUrl();
      final uri = Uri.parse('$serverUrl/health');
      final res = await http.get(uri).timeout(const Duration(seconds: 3));
      _isOnline = res.statusCode == 200;
    } catch (_) {
      _isOnline = false;
    }
    if (mounted) setState(() {});
  }

  Future<void> _handleSyncNow() async {
    setState(() => _isSyncing = true);

    final syncEngine = SyncEngine();
    final result = await syncEngine.pushPendingQueue();

    await _checkConnectivityStatus();
    final metrics = await _dbHelper.getSyncMetrics();
    final drafts = await _dbHelper.getAllDrafts(statusFilter: _activeFilter);

    setState(() {
      _isSyncing = false;
      _metrics = metrics;
      _drafts = drafts;
      if (result.success && result.totalCount > 0) {
        _lastSyncTime = DateTime.now();
      }
    });

    if (mounted) {
      if (result.success) {
        if (result.totalCount == 0) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('All local drafts are up to date. No pending items.')),
          );
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(
                'Sync complete: ${result.syncedCount} synchronized, ${result.needsReviewCount} needs review, ${result.failedCount} failed.',
              ),
              backgroundColor: result.failedCount > 0 ? Colors.orange.shade800 : Colors.green.shade800,
            ),
          );
        }
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(result.errorMessage ?? 'Sync failed. Records preserved in local encrypted storage.'),
            backgroundColor: Colors.red.shade800,
          ),
        );
      }
    }
  }

  Color _getStatusColor(String status) {
    switch (status.toUpperCase()) {
      case 'SYNCED':
        return Colors.green.shade700;
      case 'PENDING':
        return Colors.orange.shade800;
      case 'NEEDS_REVIEW':
        return Colors.purple.shade700;
      case 'FAILED':
        return Colors.red.shade700;
      default:
        return Colors.grey.shade700;
    }
  }

  IconData _getEntityIcon(String type) {
    switch (type.toUpperCase()) {
      case 'CLIENT':
      case 'PERSON':
        return Icons.person;
      case 'INTAKE':
      case 'REFERRAL':
        return Icons.assignment_outlined;
      case 'CASE_NOTE':
        return Icons.edit_note;
      case 'HOME_VISIT':
        return Icons.home_work;
      case 'FOLLOW_UP':
        return Icons.check_circle_outline;
      default:
        return Icons.folder;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Offline Workspace • $_userName'),
        backgroundColor: const Color(0xFF8B2626),
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh Status',
            onPressed: _loadDashboardData,
          ),
          IconButton(
            icon: const Icon(Icons.person),
            tooltip: 'Profile',
            onPressed: () => Navigator.pushNamed(context, '/profile'),
          ),
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Lock Vault',
            onPressed: () => Navigator.pushReplacementNamed(context, '/login'),
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _loadDashboardData,
              child: SingleChildScrollView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    // Caseworker Greeting & Connectivity Banner
                    _buildConnectivityBanner(),
                    const SizedBox(height: 16),

                    // Metrics Grid (Pending, Synced, Needs Review, Failed)
                    _buildMetricsGrid(),
                    const SizedBox(height: 16),

                    // Sync Now Action Row
                    _buildSyncActionRow(),
                    const SizedBox(height: 20),

                    // Quick Actions for Offline Draft Creation
                    const Text(
                      'Create Offline Records',
                      style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.black87),
                    ),
                    const SizedBox(height: 10),
                    _buildActionCardsGrid(),
                    const SizedBox(height: 24),

                    // Drafts Ledger Header & Filter Tabs
                    _buildDraftsSection(),
                  ],
                ),
              ),
            ),
    );
  }

  Widget _buildConnectivityBanner() {
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      color: _isOnline ? Colors.green.shade50 : Colors.amber.shade50,
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 12.0),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: _isOnline ? Colors.green.shade100 : Colors.orange.shade100,
              ),
              child: Icon(
                _isOnline ? Icons.wifi : Icons.wifi_off,
                color: _isOnline ? Colors.green.shade800 : Colors.orange.shade900,
                size: 24,
              ),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Text(
                        _isOnline ? 'Online Connected' : 'Offline Field Mode',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 15,
                          color: _isOnline ? Colors.green.shade900 : Colors.orange.shade900,
                        ),
                      ),
                      const SizedBox(width: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: _isOnline ? Colors.green.shade200 : Colors.orange.shade200,
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Text(
                          _isOnline ? 'LIVE' : 'SQLCIPHER ENCRYPTED',
                          style: TextStyle(
                            fontSize: 10,
                            fontWeight: FontWeight.bold,
                            color: _isOnline ? Colors.green.shade900 : Colors.orange.shade900,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 2),
                  Text(
                    _isOnline
                      ? 'Server reachable. Ready to sync outbox queue.'
                      : 'Changes saved safely to AES-256 local storage.',
                    style: TextStyle(fontSize: 12, color: Colors.grey.shade700),
                  ),
                ],
              ),
            ),
            IconButton(
              icon: const Icon(Icons.sync_problem, size: 20),
              tooltip: 'Check Connection',
              onPressed: _checkConnectivityStatus,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMetricsGrid() {
    return Row(
      children: [
        _buildMetricCard(
          title: 'Pending Sync',
          count: _metrics['PENDING'] ?? 0,
          color: Colors.orange.shade800,
          bgColor: Colors.orange.shade50,
          icon: Icons.hourglass_top,
          filterKey: 'PENDING',
        ),
        const SizedBox(width: 8),
        _buildMetricCard(
          title: 'Synced',
          count: _metrics['SYNCED'] ?? 0,
          color: Colors.green.shade800,
          bgColor: Colors.green.shade50,
          icon: Icons.check_circle,
          filterKey: 'SYNCED',
        ),
        const SizedBox(width: 8),
        _buildMetricCard(
          title: 'Needs Review',
          count: _metrics['NEEDS_REVIEW'] ?? 0,
          color: Colors.purple.shade800,
          bgColor: Colors.purple.shade50,
          icon: Icons.rate_review,
          filterKey: 'NEEDS_REVIEW',
        ),
        const SizedBox(width: 8),
        _buildMetricCard(
          title: 'Failed',
          count: _metrics['FAILED'] ?? 0,
          color: Colors.red.shade800,
          bgColor: Colors.red.shade50,
          icon: Icons.error_outline,
          filterKey: 'FAILED',
        ),
      ],
    );
  }

  Widget _buildMetricCard({
    required String title,
    required int count,
    required Color color,
    required Color bgColor,
    required IconData icon,
    required String filterKey,
  }) {
    final isSelected = _activeFilter == filterKey;

    return Expanded(
      child: InkWell(
        onTap: () async {
          final newFilter = _activeFilter == filterKey ? 'ALL' : filterKey;
          final drafts = await _dbHelper.getAllDrafts(statusFilter: newFilter);
          setState(() {
            _activeFilter = newFilter;
            _drafts = drafts;
          });
        },
        borderRadius: BorderRadius.circular(10),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
          decoration: BoxDecoration(
            color: bgColor,
            borderRadius: BorderRadius.circular(10),
            border: Border.all(
              color: isSelected ? color : Colors.transparent,
              width: 2,
            ),
          ),
          child: Column(
            children: [
              Icon(icon, color: color, size: 22),
              const SizedBox(height: 6),
              Text(
                '$count',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: color),
              ),
              const SizedBox(height: 2),
              Text(
                title,
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 10, fontWeight: FontWeight.w600, color: color),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSyncActionRow() {
    final pendingCount = (_metrics['PENDING'] ?? 0) + (_metrics['FAILED'] ?? 0);

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(14.0),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Synchronization Status', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                  const SizedBox(height: 4),
                  Text(
                    _lastSyncTime != null
                        ? 'Last sync: ${DateFormat("MMM d, h:mm a").format(_lastSyncTime!)}'
                        : 'No synchronization performed this session',
                    style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
                  ),
                ],
              ),
            ),
            ElevatedButton.icon(
              onPressed: _isSyncing ? null : _handleSyncNow,
              icon: _isSyncing
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                    )
                  : const Icon(Icons.cloud_upload),
              label: Text(_isSyncing ? 'Syncing...' : 'Sync Now ($pendingCount)'),
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF8B2626),
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildActionCardsGrid() {
    return Column(
      children: [
        Row(
          children: [
            _buildActionCard(
              title: 'Client Registration',
              subtitle: 'Draft Person & Client profile',
              icon: Icons.person_add_alt_1,
              color: Colors.blue.shade800,
              onTap: () async {
                final created = await Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => const ClientDraftScreen()),
                );
                if (created == true) _loadDashboardData();
              },
            ),
            const SizedBox(width: 12),
            _buildActionCard(
              title: 'Intake / Referral',
              subtitle: 'Record intake & concerns',
              icon: Icons.note_add,
              color: Colors.teal.shade800,
              onTap: () async {
                final created = await Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => const IntakeDraftScreen()),
                );
                if (created == true) _loadDashboardData();
              },
            ),
          ],
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            _buildActionCard(
              title: 'Case Note Draft',
              subtitle: 'Progress note & dictation',
              icon: Icons.edit_note,
              color: Colors.deepPurple.shade800,
              onTap: () async {
                final created = await Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => const NoteDraftScreen()),
                );
                if (created == true) _loadDashboardData();
              },
            ),
            const SizedBox(width: 12),
            _buildActionCard(
              title: 'Home Visit & Tasks',
              subtitle: 'Visits & calendar follow-ups',
              icon: Icons.calendar_month,
              color: Colors.indigo.shade800,
              onTap: () async {
                final created = await Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => const VisitDraftScreen()),
                );
                if (created == true) _loadDashboardData();
              },
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildActionCard({
    required String title,
    required String subtitle,
    required IconData icon,
    required Color color,
    required VoidCallback onTap,
  }) {
    return Expanded(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: Colors.grey.shade300),
            boxShadow: [
              BoxShadow(color: Colors.black.withValues(alpha: 0.03), blurRadius: 4, offset: const Offset(0, 2)),
            ],
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: color.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(icon, color: color, size: 24),
              ),
              const SizedBox(height: 10),
              Text(
                title,
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.black87),
              ),
              const SizedBox(height: 2),
              Text(
                subtitle,
                style: TextStyle(fontSize: 11, color: Colors.grey.shade600),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildDraftsSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              'Local Records (${_drafts.length})',
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.black87),
            ),
            if (_activeFilter != 'ALL')
              TextButton(
                onPressed: () async {
                  final drafts = await _dbHelper.getAllDrafts(statusFilter: 'ALL');
                  setState(() {
                    _activeFilter = 'ALL';
                    _drafts = drafts;
                  });
                },
                child: Text('Clear filter (${_activeFilter})'),
              ),
          ],
        ),
        const SizedBox(height: 8),

        if (_drafts.isEmpty)
          Card(
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            child: Padding(
              padding: const EdgeInsets.symmetric(vertical: 36.0, horizontal: 16.0),
              child: Column(
                children: [
                  Icon(Icons.inbox_outlined, size: 48, color: Colors.grey.shade400),
                  const SizedBox(height: 12),
                  const Text(
                    'No local records found',
                    style: TextStyle(fontWeight: FontWeight.bold, color: Colors.black54),
                  ),
                  const SizedBox(height: 4),
                  const Text(
                    'Create an offline client, intake, case note, or home visit above.',
                    style: TextStyle(fontSize: 12, color: Colors.black38),
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
            ),
          )
        else
          ListView.separated(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: _drafts.length,
            separatorBuilder: (_, __) => const SizedBox(height: 8),
            itemBuilder: (context, index) {
              final draft = _drafts[index];
              return _buildDraftCard(draft);
            },
          ),
      ],
    );
  }

  Widget _buildDraftCard(Map<String, dynamic> draft) {
    final entityType = (draft['entity_type'] as String?) ?? 'UNKNOWN';
    final status = (draft['sync_status'] as String?) ?? 'PENDING';
    final title = (draft['title'] as String?) ?? 'Untitled Draft';
    final subtitle = draft['subtitle'] as String?;
    final serverId = draft['server_id'] as String?;
    final personIdNumber = draft['person_id_number'] as String?;
    final referralNumber = draft['referral_number'] as String?;
    final errorMsg = draft['error_message'] as String?;
    final createdAt = draft['created_at'] as String?;

    String displayDate = '';
    if (createdAt != null) {
      try {
        final dt = DateTime.parse(createdAt);
        displayDate = DateFormat('MMM d, h:mm a').format(dt);
      } catch (_) {}
    }

    final isSynced = status == 'SYNCED';
    final statusColor = _getStatusColor(status);

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: statusColor.withValues(alpha: 0.3), width: 1),
      ),
      child: Padding(
        padding: const EdgeInsets.all(14.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(_getEntityIcon(entityType), color: statusColor, size: 20),
                const SizedBox(width: 8),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: Colors.grey.shade200,
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    entityType,
                    style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Colors.black87),
                  ),
                ),
                const Spacer(),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: statusColor.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Container(
                        width: 6,
                        height: 6,
                        decoration: BoxDecoration(shape: BoxShape.circle, color: statusColor),
                      ),
                      const SizedBox(width: 6),
                      Text(
                        status == 'SYNCED'
                            ? 'Synced (Server Verified)'
                            : status == 'NEEDS_REVIEW'
                                ? 'Needs Review'
                                : status == 'FAILED'
                                    ? 'Sync Failed'
                                    : 'Local Draft (Pending Sync)',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                          color: statusColor,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Text(
              title,
              style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: Colors.black87),
            ),
            if (subtitle != null && subtitle.isNotEmpty) ...[
              const SizedBox(height: 4),
              Text(
                subtitle,
                style: TextStyle(fontSize: 12, color: Colors.grey.shade700),
              ),
            ],

            // Display server permanent IDs when available
            if (personIdNumber != null) ...[
              const SizedBox(height: 6),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.green.shade50,
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(color: Colors.green.shade300),
                ),
                child: Text(
                  'Permanent Person ID: $personIdNumber',
                  style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Colors.green.shade900),
                ),
              ),
            ],

            if (referralNumber != null) ...[
              const SizedBox(height: 6),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.green.shade50,
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(color: Colors.green.shade300),
                ),
                child: Text(
                  'Referral Number: $referralNumber',
                  style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Colors.green.shade900),
                ),
              ),
            ],

            if (serverId != null && personIdNumber == null && referralNumber == null) ...[
              const SizedBox(height: 6),
              Text('Server ID: $serverId', style: TextStyle(fontSize: 11, color: Colors.grey.shade600)),
            ],

            if (errorMsg != null && errorMsg.isNotEmpty) ...[
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: status == 'NEEDS_REVIEW' ? Colors.purple.shade50 : Colors.red.shade50,
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(
                    color: status == 'NEEDS_REVIEW' ? Colors.purple.shade200 : Colors.red.shade200,
                  ),
                ),
                child: Text(
                  errorMsg,
                  style: TextStyle(
                    fontSize: 11,
                    color: status == 'NEEDS_REVIEW' ? Colors.purple.shade900 : Colors.red.shade900,
                  ),
                ),
              ),
            ],

            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  displayDate.isNotEmpty ? 'Created: $displayDate' : '',
                  style: TextStyle(fontSize: 11, color: Colors.grey.shade500),
                ),
                if (!isSynced)
                  IconButton(
                    icon: const Icon(Icons.delete_outline, size: 18, color: Colors.red),
                    tooltip: 'Discard Draft',
                    onPressed: () async {
                      final confirmed = await showDialog<bool>(
                        context: context,
                        builder: (ctx) => AlertDialog(
                          title: const Text('Discard Draft?'),
                          content: const Text('Are you sure you want to discard this local draft?'),
                          actions: [
                            TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel')),
                            TextButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Discard', style: TextStyle(color: Colors.red))),
                          ],
                        ),
                      );
                      if (confirmed == true) {
                        await _dbHelper.deleteDraft(draft['id'] as String);
                        _loadDashboardData();
                      }
                    },
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
