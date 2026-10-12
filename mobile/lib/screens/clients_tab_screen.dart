import 'package:flutter/material.dart';
import '../services/db_helper.dart';
import '../services/theme_service.dart';
import '../widgets/status_badge.dart';

class ClientsTabScreen extends StatefulWidget {
  final VoidCallback onOpenDrawer;

  const ClientsTabScreen({super.key, required this.onOpenDrawer});

  @override
  State<ClientsTabScreen> createState() => _ClientsTabScreenState();
}

class _ClientsTabScreenState extends State<ClientsTabScreen> {
  final _dbHelper = LocalDatabaseHelper.instance;
  bool _isLoading = true;
  List<Map<String, dynamic>> _clientDrafts = [];
  String _searchQuery = '';

  @override
  void initState() {
    super.initState();
    _loadClients();
  }

  Future<void> _loadClients() async {
    setState(() => _isLoading = true);
    final allDrafts = await _dbHelper.getAllDrafts();
    final clientDrafts = allDrafts.where((d) => d['entity_type'] == 'CLIENT').toList();
    if (mounted) {
      setState(() {
        _clientDrafts = clientDrafts;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    final isDark = theme.brightness == Brightness.dark;

    final filtered = _clientDrafts.where((d) {
      if (_searchQuery.isEmpty) return true;
      final title = (d['title'] as String? ?? '').toLowerCase();
      final sub = (d['subtitle'] as String? ?? '').toLowerCase();
      return title.contains(_searchQuery.toLowerCase()) || sub.contains(_searchQuery.toLowerCase());
    }).toList();

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.menu),
          tooltip: 'Open navigation menu',
          onPressed: widget.onOpenDrawer,
        ),
        title: const Text('Clients • Field Directory'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh',
            onPressed: _loadClients,
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () async {
          final created = await Navigator.pushNamed(context, '/client-draft');
          if (created == true) _loadClients();
        },
        backgroundColor: colorScheme.primary,
        foregroundColor: colorScheme.onPrimary,
        icon: const Icon(Icons.person_add),
        label: const Text('Register Client'),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _loadClients,
              child: SingleChildScrollView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    // Search box
                    TextField(
                      decoration: const InputDecoration(
                        hintText: 'Search local client drafts...',
                        prefixIcon: Icon(Icons.search),
                        isDense: true,
                      ),
                      onChanged: (val) => setState(() => _searchQuery = val),
                    ),
                    const SizedBox(height: 14),

                    // Information note
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: colorScheme.primary.withValues(alpha: 0.08),
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(
                          color: colorScheme.primary.withValues(alpha: 0.2),
                          width: 1,
                        ),
                      ),
                      child: Row(
                        children: [
                          Icon(Icons.info_outline, size: 18, color: colorScheme.primary),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Text(
                              'Offline Client Registry: New clients drafted in the field receive permanent CRBCL identifiers upon server synchronization.',
                              style: TextStyle(
                                fontSize: 12,
                                color: colorScheme.onSurface.withValues(alpha: 0.8),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),

                    // Client Drafts List
                    if (filtered.isEmpty)
                      Card(
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                          side: BorderSide(
                            color: isDark ? colorScheme.outlineVariant : CrbclTokens.lightBorder,
                            width: 1,
                          ),
                        ),
                        color: colorScheme.surfaceContainer,
                        child: Padding(
                          padding: const EdgeInsets.symmetric(vertical: 40.0, horizontal: 16.0),
                          child: Column(
                            children: [
                              Icon(
                                Icons.people_outline,
                                size: 48,
                                color: colorScheme.onSurface.withValues(alpha: 0.4),
                              ),
                              const SizedBox(height: 12),
                              Text(
                                _searchQuery.isEmpty
                                    ? 'No local client drafts found'
                                    : 'No clients matching "$_searchQuery"',
                                style: TextStyle(
                                  fontWeight: FontWeight.bold,
                                  fontSize: 14,
                                  color: colorScheme.onSurface.withValues(alpha: 0.7),
                                ),
                              ),
                              const SizedBox(height: 6),
                              Text(
                                'Tap "+ Register Client" below to draft a Person & Client registration offline.',
                                style: TextStyle(
                                  fontSize: 12,
                                  color: colorScheme.onSurface.withValues(alpha: 0.5),
                                ),
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
                        itemCount: filtered.length,
                        separatorBuilder: (_, __) => const SizedBox(height: 8),
                        itemBuilder: (context, index) {
                          final draft = filtered[index];
                          final title = draft['title'] as String? ?? 'Client Draft';
                          final subtitle = draft['subtitle'] as String? ?? '';
                          final status = draft['sync_status'] as String? ?? 'PENDING';
                          final personIdNumber = draft['person_id_number'] as String?;

                          return Card(
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12),
                              side: BorderSide(
                                color: isDark ? colorScheme.outlineVariant : CrbclTokens.lightBorder,
                                width: 1,
                              ),
                            ),
                            color: colorScheme.surfaceContainer,
                            child: Padding(
                              padding: const EdgeInsets.all(14.0),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    children: [
                                      CircleAvatar(
                                        radius: 18,
                                        backgroundColor: colorScheme.primary.withValues(alpha: 0.15),
                                        child: Icon(Icons.person, size: 20, color: colorScheme.primary),
                                      ),
                                      const SizedBox(width: 10),
                                      Expanded(
                                        child: Column(
                                          crossAxisAlignment: CrossAxisAlignment.start,
                                          children: [
                                            Text(
                                              title,
                                              style: TextStyle(
                                                fontWeight: FontWeight.bold,
                                                fontSize: 14,
                                                color: colorScheme.onSurface,
                                              ),
                                              maxLines: 1,
                                              overflow: TextOverflow.ellipsis,
                                            ),
                                            if (subtitle.isNotEmpty)
                                              Text(
                                                subtitle,
                                                style: TextStyle(
                                                  fontSize: 11,
                                                  color: colorScheme.onSurface.withValues(alpha: 0.6),
                                                ),
                                                maxLines: 1,
                                                overflow: TextOverflow.ellipsis,
                                              ),
                                          ],
                                        ),
                                      ),
                                      StatusBadge(status: status, compact: true),
                                    ],
                                  ),
                                  if (personIdNumber != null) ...[
                                    const SizedBox(height: 8),
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                      decoration: BoxDecoration(
                                        color: CrbclTokens.statusSuccess.withValues(alpha: 0.12),
                                        borderRadius: BorderRadius.circular(6),
                                      ),
                                      child: Text(
                                        'Permanent ID: $personIdNumber',
                                        style: const TextStyle(
                                          fontSize: 11,
                                          fontWeight: FontWeight.bold,
                                          color: CrbclTokens.statusSuccess,
                                        ),
                                      ),
                                    ),
                                  ],
                                ],
                              ),
                            ),
                          );
                        },
                      ),
                  ],
                ),
              ),
            ),
    );
  }
}
