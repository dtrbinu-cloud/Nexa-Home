import 'package:flutter/material.dart';
import 'package:app/components/app_bottom_nav.dart';
import 'package:app/screens/tabs/assistant_tab.dart';
import 'package:app/screens/tabs/cameras_tab.dart';
import 'package:app/screens/tabs/home_tab.dart';
import 'package:app/screens/tabs/more_tab.dart';

class ShellScreen extends StatefulWidget {
  final int initialTab;
  const ShellScreen({super.key, this.initialTab = 0});

  @override
  State<ShellScreen> createState() => _ShellScreenState();
}

class _ShellScreenState extends State<ShellScreen> {
  late int _currentIndex;

  @override
  void initState() {
    super.initState();
    _currentIndex = widget.initialTab;
  }

  final _tabs = const [
    HomeTab(),
    CamerasTab(),
    AssistantTab(),
    MoreTab(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: _tabs,
      ),
      bottomNavigationBar: AppBottomNav(
        currentIndex: _currentIndex,
        onTap: (idx) => setState(() => _currentIndex = idx),
      ),
    );
  }
}

