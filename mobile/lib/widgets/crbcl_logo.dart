import 'package:flutter/material.dart';

enum CrbclLogoVariant {
  full,    // Full lockup with typography (crbcl_logo.png or crbcl_logo_dark.png)
  emblem,  // Paw & moccasins emblem mark (crbcl_emblem.png)
}

/// Official CRBCL Branding Logo Component.
/// Automatically adapts between light and dark backgrounds using the approved
/// website brand assets.
class CrbclLogo extends StatelessWidget {
  final double height;
  final double? width;
  final CrbclLogoVariant variant;
  final BoxFit fit;

  const CrbclLogo({
    super.key,
    this.height = 48,
    this.width,
    this.variant = CrbclLogoVariant.full,
    this.fit = BoxFit.contain,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    final String assetPath;
    if (variant == CrbclLogoVariant.emblem) {
      assetPath = 'assets/branding/crbcl_emblem.png';
    } else {
      assetPath = isDark
          ? 'assets/branding/crbcl_logo_dark.png'
          : 'assets/branding/crbcl_logo.png';
    }

    return Image.asset(
      assetPath,
      height: height,
      width: width,
      fit: fit,
      semanticLabel: "Chief Red Bear Children's Lodge Official Logo",
      errorBuilder: (context, error, stackTrace) {
        // Fallback: render graceful branded text lockup if asset loading fails
        return Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.wb_sunny_rounded,
              size: height * 0.7,
              color: Theme.of(context).colorScheme.primary,
            ),
            const SizedBox(width: 8),
            Text(
              'CRBCL',
              style: TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: height * 0.45,
                color: Theme.of(context).colorScheme.primary,
                letterSpacing: 1.2,
              ),
            ),
          ],
        );
      },
    );
  }
}
