import AppKit
import Foundation
import Vision

// macOS Vision OCR for one local image. Invoked by ocr_frames.py when swiftc exists.
// Prints recognized lines to stdout. Does not take a URL.

if CommandLine.arguments.count < 2 {
    fputs("usage: ocr_vision <image>\n", stderr)
    exit(2)
}

let url = URL(fileURLWithPath: CommandLine.arguments[1])
guard let image = NSImage(contentsOf: url) else {
    fputs("vision: cannot load image\n", stderr)
    exit(2)
}

var rect = CGRect(origin: .zero, size: image.size)
guard let cg = image.cgImage(forProposedRect: &rect, context: nil, hints: nil) else {
    fputs("vision: cannot read CGImage\n", stderr)
    exit(2)
}

let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.usesLanguageCorrection = false
if #available(macOS 11.0, *) {
    request.recognitionLanguages = ["zh-Hans", "zh-Hant", "en-US"]
}

let handler = VNImageRequestHandler(cgImage: cg, options: [:])
do {
    try handler.perform([request])
} catch {
    fputs("vision: \(error.localizedDescription)\n", stderr)
    exit(1)
}

let lines = (request.results ?? []).compactMap { observation -> String? in
    observation.topCandidates(1).first?.string
}
print(lines.joined(separator: "\n"))
