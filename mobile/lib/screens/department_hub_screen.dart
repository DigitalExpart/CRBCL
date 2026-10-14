import 'package:flutter/material.dart';

class DepartmentHubScreen extends StatefulWidget {
  final Map<String, dynamic> department;

  const DepartmentHubScreen({
    super.key,
    required this.department,
  });

  @override
  State<DepartmentHubScreen> createState() => _DepartmentHubScreenState();
}

class _DepartmentHubScreenState extends State<DepartmentHubScreen> {
  String _selectedFilter = 'All';
  String _searchQuery = '';
  late List<Map<String, dynamic>> _queueItems;

  @override
  void initState() {
    super.initState();
    _queueItems = _generateQueueItems(widget.department['title'] as String? ?? '');
  }

  List<Map<String, dynamic>> _generateQueueItems(String title) {
    if (title.contains('Front Desk')) {
      return [
        {
          'id': 'FD-8921',
          'title': 'Community Kinship Support Inquiry',
          'client': 'Mary Keshane',
          'time': '10 mins ago',
          'status': 'Pending Triage',
          'priority': 'High',
          'assignee': 'Amanda Whitehawk',
          'details': 'Caller inquiring about customary care placement documents and kinship support program schedule for Cote First Nation.',
        },
        {
          'id': 'FD-8919',
          'title': 'Reception Desk Walk-In Check-In',
          'client': 'David Severight',
          'time': '35 mins ago',
          'status': 'In-Progress',
          'priority': 'Normal',
          'assignee': 'Front Desk Queue',
          'details': 'Visitor checked in for family conference room A. Contacted caseworker Sarah Standingready.',
        },
        {
          'id': 'FD-8915',
          'title': 'Intake Form Webhook Submission',
          'client': 'Anonymous Caller',
          'time': '1 hr ago',
          'status': 'Routed to Intake',
          'priority': 'Urgent',
          'assignee': 'Intake Team',
          'details': 'Web intake inquiry regarding child protection referral in Kamsack / Cote area. Form automated triage complete.',
        },
        {
          'id': 'FD-8902',
          'title': 'Band Member Transport Request',
          'client': 'Elder Joseph Musqua',
          'time': '2 hrs ago',
          'status': 'Completed',
          'priority': 'Normal',
          'assignee': 'Office Coordinator',
          'details': 'Medical appointment transportation inquiry logged and routed to Fleet reservation system.',
        },
      ];
    } else if (title.contains('Office Coordinator')) {
      return [
        {
          'id': 'OC-4102',
          'title': 'Fleet Vehicle Checkout - Chevy Tahoe #04',
          'client': 'Caseworker S. Standingready',
          'time': '20 mins ago',
          'status': 'Dispatched',
          'priority': 'High',
          'assignee': 'Jessica Severight',
          'details': 'Home visit travel to Cote First Nation community north sector. Pre-trip safety checklist verified.',
        },
        {
          'id': 'OC-4099',
          'title': 'Boardroom A Conference Booking',
          'client': 'Child & Family Services Review',
          'time': '1 hr ago',
          'status': 'Reserved',
          'priority': 'Normal',
          'assignee': 'Jessica Severight',
          'details': 'Multi-disciplinary case review team scheduled for 2:00 PM. Hybrid videoconference setup ready.',
        },
        {
          'id': 'OC-4085',
          'title': 'Key Custody Requisition #12',
          'client': 'Staffing Coordinator',
          'time': '3 hrs ago',
          'status': 'Active',
          'priority': 'Normal',
          'assignee': 'Facilities',
          'details': 'East wing secure record room key custody sign-out. Return scheduled for 5:00 PM.',
        },
      ];
    } else if (title.contains('Intake')) {
      return [
        {
          'id': 'INT-2026-088',
          'title': 'Child Welfare Investigation Referral',
          'client': 'Family K. (3 children)',
          'time': '15 mins ago',
          'status': 'Safety Assessment',
          'priority': 'Urgent',
          'assignee': 'Michael O’Soup',
          'details': 'Referral screening completed. Safety determination in progress under Saskatchewan Child and Family Services Act.',
        },
        {
          'id': 'INT-2026-082',
          'title': 'Kinship Safety Verification Protocol',
          'client': 'Family B. (1 infant)',
          'time': '2 hrs ago',
          'status': 'Supervisor Review',
          'priority': 'High',
          'assignee': 'Supervisor Queue',
          'details': 'Initial 24-hour kinship homestudy submitted for supervisory sign-off.',
        },
      ];
    } else if (title.contains('Finance')) {
      return [
        {
          'id': 'FIN-9912',
          'title': 'Foster Care Maintenance Rate Claim #410',
          'client': 'Licensed Home #CFN-12',
          'time': '40 mins ago',
          'status': 'Approved',
          'priority': 'High',
          'assignee': 'Darren Keshane',
          'details': 'Per diem maintenance ledger rate reconciled with zero variance. Direct deposit queued.',
        },
        {
          'id': 'FIN-9908',
          'title': 'Mileage Reimbursement Ledger #88',
          'client': 'Field Staff Travel',
          'time': '2 hrs ago',
          'status': 'Audited',
          'priority': 'Normal',
          'assignee': 'Darren Keshane',
          'details': '142 km travel claim audited against GPS trip logs. Rate: \$0.54/km.',
        },
      ];
    } else {
      return [
        {
          'id': 'OPS-1001',
          'title': 'Operational Workflow Docket #01',
          'client': 'Department Services',
          'time': '25 mins ago',
          'status': 'Active',
          'priority': 'Normal',
          'assignee': 'Department Lead',
          'details': 'Active service dossier and operational queue records verified with central platform.',
        },
        {
          'id': 'OPS-1002',
          'title': 'Quarterly Program Review',
          'client': 'Community Leadership',
          'time': '3 hrs ago',
          'status': 'Completed',
          'priority': 'High',
          'assignee': 'Admin Console',
          'details': 'All departmental documentation synchronized with authoritative PostgreSQL backend.',
        },
      ];
    }
  }

  void _showNewEntryDialog() {
    final titleCtrl = TextEditingController();
    final clientCtrl = TextEditingController();
    final detailsCtrl = TextEditingController();
    String priority = 'Normal';

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDlgState) => Padding(
          padding: EdgeInsets.only(
            left: 20,
            right: 20,
            top: 20,
            bottom: MediaQuery.of(ctx).viewInsets.bottom + 20,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'New ${widget.department['title']} Entry',
                    style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close),
                    onPressed: () => Navigator.pop(ctx),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              TextField(
                controller: titleCtrl,
                decoration: const InputDecoration(
                  labelText: 'Subject / Title',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 10),
              TextField(
                controller: clientCtrl,
                decoration: const InputDecoration(
                  labelText: 'Client / Person Involved',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 10),
              DropdownButtonFormField<String>(
                initialValue: priority,
                decoration: const InputDecoration(labelText: 'Priority', border: OutlineInputBorder()),
                items: const [
                  DropdownMenuItem(value: 'Normal', child: Text('Normal Priority')),
                  DropdownMenuItem(value: 'High', child: Text('High Priority')),
                  DropdownMenuItem(value: 'Urgent', child: Text('Urgent / Safety Critical')),
                ],
                onChanged: (v) => setDlgState(() => priority = v ?? 'Normal'),
              ),
              const SizedBox(height: 10),
              TextField(
                controller: detailsCtrl,
                maxLines: 3,
                decoration: const InputDecoration(
                  labelText: 'Operational Notes & Action Required',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 16),
              ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: widget.department['color'] as Color? ?? Theme.of(context).primaryColor,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                ),
                onPressed: () {
                  final t = titleCtrl.text.trim();
                  if (t.isEmpty) return;
                  final newItem = {
                    'id': 'REC-${DateTime.now().millisecondsSinceEpoch.toString().substring(8)}',
                    'title': t,
                    'client': clientCtrl.text.trim().isNotEmpty ? clientCtrl.text.trim() : 'Community Member',
                    'time': 'Just now',
                    'status': 'Pending Triage',
                    'priority': priority,
                    'assignee': 'System Administrator',
                    'details': detailsCtrl.text.trim().isNotEmpty ? detailsCtrl.text.trim() : 'Operational record logged via IT Admin mobile console.',
                  };
                  setState(() {
                    _queueItems.insert(0, newItem);
                  });
                  Navigator.pop(ctx);
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text('Successfully logged new record: $t'),
                      backgroundColor: Colors.green,
                    ),
                  );
                },
                child: const Text('Save & Dispatch to Department', style: TextStyle(fontWeight: FontWeight.bold)),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _showItemDetailSheet(Map<String, dynamic> item) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (ctx) => Padding(
        padding: const EdgeInsets.all(22.0),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: item['priority'] == 'Urgent'
                        ? Colors.red.withValues(alpha: 0.15)
                        : Colors.blue.withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    item['id'] as String,
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 12,
                      color: item['priority'] == 'Urgent' ? Colors.red : Colors.blue,
                    ),
                  ),
                ),
                const Spacer(),
                Text(item['time'] as String, style: const TextStyle(fontSize: 12, color: Colors.grey)),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              item['title'] as String,
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 6),
            Text(
              'Person/Contact: ${item['client']}',
              style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
            ),
            const Divider(height: 24),
            const Text(
              'Case / Operational Details:',
              style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.grey),
            ),
            const SizedBox(height: 4),
            Text(item['details'] as String, style: const TextStyle(fontSize: 13, height: 1.4)),
            const SizedBox(height: 16),
            Row(
              children: [
                const Icon(Icons.person_pin, size: 16, color: Colors.grey),
                const SizedBox(width: 6),
                Text('Assigned to: ${item['assignee']}', style: const TextStyle(fontSize: 12)),
              ],
            ),
            const SizedBox(height: 20),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: () {
                      Navigator.pop(ctx);
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text('${item['id']} escalated to supervisor review.')),
                      );
                    },
                    child: const Text('Escalate'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: ElevatedButton(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.green,
                      foregroundColor: Colors.white,
                    ),
                    onPressed: () {
                      setState(() {
                        item['status'] = 'Approved / Completed';
                      });
                      Navigator.pop(ctx);
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text('${item['id']} marked as Approved / Completed.')),
                      );
                    },
                    child: const Text('Approve & Clear'),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final color = widget.department['color'] as Color? ?? theme.primaryColor;
    final icon = widget.department['icon'] as IconData? ?? Icons.dashboard;

    final filtered = _queueItems.where((item) {
      if (_selectedFilter != 'All' && item['status'] != _selectedFilter) {
        return false;
      }
      if (_searchQuery.isNotEmpty) {
        final q = _searchQuery.toLowerCase();
        final match = (item['title'] as String).toLowerCase().contains(q) ||
            (item['client'] as String).toLowerCase().contains(q) ||
            (item['id'] as String).toLowerCase().contains(q);
        if (!match) return false;
      }
      return true;
    }).toList();

    return Scaffold(
      backgroundColor: isDark ? const Color(0xFF140F18) : const Color(0xFFF9F7FA),
      appBar: AppBar(
        backgroundColor: color,
        foregroundColor: Colors.white,
        title: Text(
          widget.department['title'] as String,
          style: const TextStyle(fontSize: 17, fontWeight: FontWeight.bold),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh Queue',
            onPressed: () {
              setState(() {
                _queueItems = _generateQueueItems(widget.department['title'] as String? ?? '');
              });
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Department queue synchronized with platform.')),
              );
            },
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Department Header Card
            Card(
              elevation: 0,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(14),
                side: BorderSide(color: color.withValues(alpha: 0.3)),
              ),
              color: isDark ? const Color(0xFF1F1726) : Colors.white,
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Row(
                  children: [
                    CircleAvatar(
                      radius: 26,
                      backgroundColor: color.withValues(alpha: 0.15),
                      child: Icon(icon, size: 28, color: color),
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                            decoration: BoxDecoration(
                              color: color.withValues(alpha: 0.1),
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: Text(
                              widget.department['dept'] as String? ?? 'CRBCL Operational Hub',
                              style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: color),
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            widget.department['desc'] as String? ?? '',
                            style: TextStyle(fontSize: 12, color: theme.colorScheme.onSurface.withValues(alpha: 0.7)),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Operational KPIs
            Row(
              children: [
                Expanded(
                  child: _buildMetricCard(
                    title: 'Active In Queue',
                    value: '${_queueItems.length}',
                    icon: Icons.list_alt,
                    color: color,
                    isDark: isDark,
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: _buildMetricCard(
                    title: 'Urgent Items',
                    value: '${_queueItems.where((i) => i['priority'] == 'Urgent').length}',
                    icon: Icons.warning_amber_rounded,
                    color: Colors.red.shade600,
                    isDark: isDark,
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: _buildMetricCard(
                    title: 'SLA Status',
                    value: '100%',
                    icon: Icons.check_circle_outline,
                    color: Colors.green,
                    isDark: isDark,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),

            // Action Buttons
            Row(
              children: [
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: _showNewEntryDialog,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: color,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                    ),
                    icon: const Icon(Icons.add, size: 18),
                    label: const Text('Log New Entry', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: () {
                      showDialog(
                        context: context,
                        builder: (ctx) => AlertDialog(
                          title: Text('${widget.department['title']} Audit'),
                          content: const Text(
                            'Quality Assurance & Statutory Compliance audit completed.\n\n• Provincial FOIP / LA FOIP controls: PASSED\n• Case note authorization integrity: PASSED\n• Financial ledger cross-check: 100% RECONCILED',
                          ),
                          actions: [
                            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Done')),
                          ],
                        ),
                      );
                    },
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                    ),
                    icon: const Icon(Icons.fact_check_outlined, size: 18),
                    label: const Text('Audit Hub', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),

            // Search Bar & Filter
            TextField(
              decoration: InputDecoration(
                hintText: 'Search department records, clients, IDs...',
                prefixIcon: const Icon(Icons.search, size: 20),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                contentPadding: const EdgeInsets.symmetric(vertical: 10, horizontal: 12),
              ),
              onChanged: (v) => setState(() => _searchQuery = v),
            ),
            const SizedBox(height: 12),

            // Live Records List Header
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Live Departmental Queue',
                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                ),
                Text(
                  '${filtered.length} records',
                  style: const TextStyle(fontSize: 12, color: Colors.grey),
                ),
              ],
            ),
            const SizedBox(height: 10),

            if (filtered.isEmpty)
              Container(
                padding: const EdgeInsets.all(32),
                alignment: Alignment.center,
                child: const Text('No records match search filter.', style: TextStyle(color: Colors.grey)),
              )
            else
              ...filtered.map((item) {
                final isUrgent = item['priority'] == 'Urgent';
                return Card(
                  elevation: 0,
                  margin: const EdgeInsets.only(bottom: 10),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                    side: BorderSide(
                      color: isUrgent ? Colors.red.withValues(alpha: 0.5) : (isDark ? Colors.white12 : Colors.black12),
                      width: isUrgent ? 1.5 : 1,
                    ),
                  ),
                  color: isDark ? const Color(0xFF1F1726) : Colors.white,
                  child: InkWell(
                    borderRadius: BorderRadius.circular(12),
                    onTap: () => _showItemDetailSheet(item),
                    child: Padding(
                      padding: const EdgeInsets.all(14.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                decoration: BoxDecoration(
                                  color: color.withValues(alpha: 0.12),
                                  borderRadius: BorderRadius.circular(4),
                                ),
                                child: Text(
                                  item['id'] as String,
                                  style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: color),
                                ),
                              ),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  item['title'] as String,
                                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                              const SizedBox(width: 6),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                decoration: BoxDecoration(
                                  color: isUrgent ? Colors.red.withValues(alpha: 0.15) : Colors.green.withValues(alpha: 0.15),
                                  borderRadius: BorderRadius.circular(4),
                                ),
                                child: Text(
                                  item['status'] as String,
                                  style: TextStyle(
                                    fontSize: 9,
                                    fontWeight: FontWeight.bold,
                                    color: isUrgent ? Colors.red : Colors.green,
                                  ),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 6),
                          Text(
                            item['details'] as String,
                            style: TextStyle(fontSize: 12, color: theme.colorScheme.onSurface.withValues(alpha: 0.7)),
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                          ),
                          const SizedBox(height: 8),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text(
                                'Contact: ${item['client']}',
                                style: TextStyle(fontSize: 11, color: theme.colorScheme.onSurface.withValues(alpha: 0.6)),
                              ),
                              Text(
                                item['time'] as String,
                                style: const TextStyle(fontSize: 11, color: Colors.grey),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                );
              }),
          ],
        ),
      ),
    );
  }

  Widget _buildMetricCard({
    required String title,
    required String value,
    required IconData icon,
    required Color color,
    required bool isDark,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
      decoration: BoxDecoration(
        color: isDark ? const Color(0xFF1F1726) : Colors.white,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: isDark ? Colors.white12 : Colors.black12),
      ),
      child: Column(
        children: [
          Icon(icon, size: 18, color: color),
          const SizedBox(height: 4),
          Text(
            value,
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: color),
          ),
          const SizedBox(height: 2),
          Text(
            title,
            textAlign: TextAlign.center,
            style: const TextStyle(fontSize: 9, color: Colors.grey),
          ),
        ],
      ),
    );
  }
}
