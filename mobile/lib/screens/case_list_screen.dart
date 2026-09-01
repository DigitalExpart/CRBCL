import 'package:flutter/material.dart';

class CaseListScreen extends StatelessWidget {
  const CaseListScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final offlineCases = [
      {'number': 'CASE-2026-101', 'title': 'Bear Family Wellness & Support', 'stage': 'INVESTIGATION'},
      {'number': 'CASE-2026-104', 'title': 'Johnston Permanency Plan', 'stage': 'FAMILY_PREVENTION'},
    ];

    return Scaffold(
      appBar: AppBar(title: const Text('Cached Assigned Cases')),
      body: ListView.builder(
        itemCount: offlineCases.length,
        itemBuilder: (context, index) {
          final c = offlineCases[index];
          return ListTile(
            leading: const Icon(Icons.folder, color: Colors.indigo),
            title: Text(c['title']!),
            subtitle: Text('${c['number']} • ${c['stage']}'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () {
              Navigator.pushNamed(context, '/note-draft');
            },
          );
        },
      ),
    );
  }
}
