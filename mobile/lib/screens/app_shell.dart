import 'package:flutter/material.dart';
import '../widgets/app_drawer.dart';
import 'home_dashboard_screen.dart';
import 'clients_tab_screen.dart';
import 'case_list_screen.dart';
import 'field_dashboard.dart';
import 'profile_screen.dart';

/// Authenticated Application Shell for the CRBCL Mobile Platform.
/// Provides persistent bottom navigation and integrated drawer navigation
/// across the primary operational workspaces.
class AppShell extends StatefulWidget {
  final int initialTab;

  const AppShell({super.key, this.initialTab = 0});

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
  final GlobalKey<ScaffoldState> _scaffoldKey = GlobalKey<ScaffoldState>();
  late int _currentIndex;

  @override
  void initState() {
    super.initState();
    _currentIndex = widget.initialTab;
  }

  void _openDrawer() {
    _scaffoldKey.currentState?.openDrawer();
  }

  void _onTabSelected(int index) {
    setState(() => _currentIndex = index);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    // The 5 primary workspaces
    final tabs = [
      HomeDashboardScreen(
        onOpenDrawer: _openDrawer,
        onNavigateTab: _onTabSelected,
      ),
      ClientsTabScreen(
        onOpenDrawer: _openDrawer,
      ),
      CaseListScreen(
        onOpenDrawer: _openDrawer,
      ),
      FieldDashboardScreen(
        onOpenDrawer: _openDrawer,
      ),
      const ProfileScreen(),
    ];

    return Scaffold(
      key: _scaffoldKey,
      drawer: AppDrawer(
        currentTabIndex: _currentIndex,
        onTabSelected: _onTabSelected,
      ),
      body: IndexedStack(
        index: _currentIndex,
        children: tabs,
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: _onTabSelected,
        type: BottomNavigationBarType.fixed,
        selectedItemColor: colorScheme.primary,
        unselectedItemColor: theme.brightness == Brightness.dark
            ? colorScheme.onSurface.withValues(alpha: 0.5)
            : colorScheme.onSurface.withValues(alpha: 0.6),
        selectedFontSize: 11,
        unselectedFontSize: 11,
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.dashboard_outlined),
            activeIcon: Icon(Icons.dashboard),
            label: 'Home',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.people_outline),
            activeIcon: Icon(Icons.people),
            label: 'Clients',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.folder_outlined),
            activeIcon: Icon(Icons.folder),
            label: 'Cases',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.cloud_sync_outlined),
            activeIcon: Icon(Icons.cloud_sync),
            label: 'Offline',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.more_horiz_outlined),
            activeIcon: Icon(Icons.more_horiz),
            label: 'More',
          ),
        ],
      ),
    );
  }
}
