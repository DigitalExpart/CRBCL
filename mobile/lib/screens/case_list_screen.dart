import 'package:flutter/material.dart';
import '../services/db_helper.dart';
import '../services/theme_service.dart';
import '../widgets/status_badge.dart';

class CaseListScreen extends StatefulWidget {
  final VoidCallback? onOpenDrawer;

  const CaseListScreen({super.key, this.onOpenDrawer});

  @override
  State<CaseListScreen> createState() => _CaseListScreenState();
}

class _CaseListScreenState extends State<CaseListScreen> {
  final _dbHelper = LocalDatabaseHelper.instance;
  bool _isLoading = true;
  List<Map<String, dynamic>> _caseDrafts = [];

  @override
  void initState() {
    super.initState();
    _loadCaseNotes();
  }

  Future<void> _loadCaseNotes() async {
    setState(() => _isLoading = true);
    final allDrafts = await _dbHelper.getAllDrafts();
    final caseDrafts = allDrafts.where((d) => d['entity_type'] == 'CASE_NOTE').toList();
    if (mounted) {
      setState(() {
        _caseDrafts = caseDrafts;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    final isDark = theme.brightness == Brightness.dark;

    return Scaffold(
      appBar: AppBar(
        leading: widget.onOpenDrawer != null
            ? IconButton(
                icon: const Icon(Icons.menu),
                tooltip: 'Open navigation menu',
                onPressed: widget.onOpenDrawer,
              )
            : const BackButton(),
        title: const Text('Cases & Progress Notes'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh',
            onPressed: _loadCaseNotes,
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () async {
          final created = await Navigator.pushNamed(context, '/note-draft');
          if (created == true) _loadCaseNotes();
        },
        backgroundColor: colorScheme.primary,
        foregroundColor: colorScheme.onPrimary,
        icon: const Icon(Icons.note_add),
        label: const Text('New Case Note'),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _loadCaseNotes,
              child: SingleChildScrollView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    // Context Information Card
                    Container(
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: colorScheme.primary.withValues(alpha: 0.08),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(
                          color: colorScheme.primary.withValues(alpha: 0.2),
                          width: 1,
                        ),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Icon(Icons.folder_shared_outlined, size: 20, color: colorScheme.primary),
                              const SizedBox(width: 8),
                              Text(
                                'Field Case Workspace',
                                style: TextStyle(
                                  fontWeight: FontWeight.bold,
                                  fontSize: 14,
                                  color: colorScheme.onSurface,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 6),
                          Text(
                            'Draft case observations, progress notes, and field dictations. '
                            'Records are encrypted with SQLCipher and securely submitted upon synchronization.',
                            style: TextStyle(
                              fontSize: 12,
                              color: colorScheme.onSurface.withValues(alpha: 0.75),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),

                    // Case Notes List
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          'Local Case Note Drafts (${_caseDrafts.length})',
                          style: TextStyle(
                            fontSize: 15,
                            fontWeight: FontWeight.bold,
                            color: colorScheme.onSurface,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),

                    if (_caseDrafts.isEmpty)
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
                                Icons.note_outlined,
                                size: 48,
                                color: colorScheme.onSurface.withValues(alpha: 0.4),
                              ),
                              const SizedBox(height: 12),
                              Text(
                                'No local case note drafts',
                                style: TextStyle(
                                  fontWeight: FontWeight.bold,
                                  fontSize: 14,
                                  color: colorScheme.onSurface.withValues(alpha: 0.7),
                                ),
                              ),
                              const SizedBox(height: 6),
                              Text(
                                'Tap "+ New Case Note" to record a progress note in the field.',
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
                        itemCount: _caseDrafts.length,
                        separatorBuilder: (_, __) => const SizedBox(height: 8),
                        itemBuilder: (context, index) {
                          final draft = _caseDrafts[index];
                          final title = draft['title'] as String? ?? 'Untitled Note';
                          final subtitle = draft['subtitle'] as String? ?? '';
                          final status = draft['sync_status'] as String? ?? 'PENDING';

                          return Card(
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12),
                              side: BorderSide(
                                color: isDark ? colorScheme.outlineVariant : CrbclTokens.lightBorder,
                                width: 1,
                              ),
                            ),
                            color: colorScheme.surfaceContainer,
                            child: ListTile(
                              leading: CircleAvatar(
                                radius: 18,
                                backgroundColor: const Color(0xFF7C3AED).withValues(alpha: 0.15),
                                child: const Icon(Icons.edit_note, size: 20, color: Color(0xFF7C3AED)),
                              ),
                              title: Text(
                                title,
                                style: TextStyle(
                                  fontWeight: FontWeight.bold,
                                  fontSize: 14,
                                  color: colorScheme.onSurface,
                                ),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                              subtitle: subtitle.isNotEmpty
                                  ? Text(
                                      subtitle,
                                      style: TextStyle(
                                        fontSize: 11,
                                        color: colorScheme.onSurface.withValues(alpha: 0.6),
                                      ),
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                    )
                                  : null,
                              trailing: StatusBadge(status: status, compact: true),
                              onTap: () {
                                Navigator.pushNamed(context, '/note-draft');
                              },
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
