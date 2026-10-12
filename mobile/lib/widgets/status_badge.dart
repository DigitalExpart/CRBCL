import 'package:flutter/material.dart';
import '../services/theme_service.dart';

/// Reusable status badge with dot indicator and theme-aware colors.
/// Prevents layout overflow by using flexible sizing and clean typography.
class StatusBadge extends StatelessWidget {
  final String status;
  final bool compact;

  const StatusBadge({
    super.key,
    required this.status,
    this.compact = false,
  });

  Color _getStatusColor(BuildContext context, String st) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    switch (st.toUpperCase()) {
      case 'SYNCED':
        return isDark ? CrbclTokens.statusSuccessDark : CrbclTokens.statusSuccess;
      case 'PENDING':
        return isDark ? CrbclTokens.statusWarningDark : CrbclTokens.statusWarning;
      case 'NEEDS_REVIEW':
        return isDark ? CrbclTokens.statusReviewDark : CrbclTokens.statusReview;
      case 'FAILED':
        return isDark ? CrbclTokens.statusErrorDark : CrbclTokens.statusError;
      default:
        return isDark ? CrbclTokens.darkMutedForeground : CrbclTokens.lightMutedForeground;
    }
  }

  String _getStatusLabel(String st) {
    switch (st.toUpperCase()) {
      case 'SYNCED':
        return compact ? 'Synced' : 'Server Verified';
      case 'PENDING':
        return compact ? 'Pending' : 'Pending Sync';
      case 'NEEDS_REVIEW':
        return 'Needs Review';
      case 'FAILED':
        return 'Sync Failed';
      default:
        return st;
    }
  }

  @override
  Widget build(BuildContext context) {
    final color = _getStatusColor(context, status);
    final label = _getStatusLabel(status);

    return Container(
      padding: EdgeInsets.symmetric(
        horizontal: compact ? 6 : 8,
        vertical: compact ? 2 : 4,
      ),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withValues(alpha: 0.25), width: 1),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 6,
            height: 6,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: color,
            ),
          ),
          const SizedBox(width: 5),
          Flexible(
            child: Text(
              label,
              style: TextStyle(
                fontSize: compact ? 10 : 11,
                fontWeight: FontWeight.w600,
                color: color,
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }
}
