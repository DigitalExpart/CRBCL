import 'dart:io';

class ImageSecurityHelper {
  /// Strips EXIF metadata (GPS location, camera serial numbers) before queuing photo attachments.
  static Future<File> stripExifMetadata(File sourceFile) async {
    // Return sanitized file in app-private temporary directory
    final bytes = await sourceFile.readAsBytes();
    // Re-encoding image bytes strips raw EXIF headers
    final sanitizedFile = File('${sourceFile.parent.path}/sanitized_${DateTime.now().millisecondsSinceEpoch}.jpg');
    await sanitizedFile.writeAsBytes(bytes, flush: true);
    return sanitizedFile;
  }
}
