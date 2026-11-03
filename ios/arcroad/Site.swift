import Foundation
import UniformTypeIdentifiers
import WebKit

/// The copy of arcroad.org bundled in the app (see the "Bundle the arcroad site" build phase).
enum Site {
    static let scheme = "arcroad"
    static var root: URL { Bundle.main.resourceURL!.appendingPathComponent("site", isDirectory: true) }
    static func url(_ path: String) -> URL { URL(string: "\(scheme)://app/\(path)")! }
    static func file(_ path: String) -> URL { root.appendingPathComponent(path) }
}

/// Serves the bundled site to the web view under arcroad://app/, with byte ranges so the films can play.
/// Only files inside the bundled site are served; nothing is fetched from the network here.
final class SiteSchemeHandler: NSObject, WKURLSchemeHandler {
    private static let types: [String: String] = [
        "html": "text/html; charset=utf-8", "js": "text/javascript; charset=utf-8", "css": "text/css; charset=utf-8",
        "json": "application/json", "svg": "image/svg+xml", "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
        "webp": "image/webp", "mp4": "video/mp4", "woff2": "font/woff2", "txt": "text/plain; charset=utf-8", "xml": "application/xml",
    ]

    func webView(_ webView: WKWebView, start task: WKURLSchemeTask) {
        guard let url = task.request.url else { task.didFailWithError(URLError(.badURL)); return }
        var path = url.path
        if path.isEmpty || path.hasSuffix("/") { path += "index.html" }
        let rel = String(path.drop(while: { $0 == "/" }))
        var file = Site.root.appendingPathComponent(rel).standardizedFileURL
        var isDir: ObjCBool = false
        if FileManager.default.fileExists(atPath: file.path, isDirectory: &isDir), isDir.boolValue {
            file = file.appendingPathComponent("index.html")
        }
        guard file.path.hasPrefix(Site.root.standardizedFileURL.path),
              let handle = try? FileHandle(forReadingFrom: file) else {
            respond(task, url: url, status: 404, headers: ["Content-Type": "text/plain"], body: Data("Not in the app.".utf8))
            return
        }
        defer { try? handle.close() }
        let size = (try? file.resourceValues(forKeys: [.fileSizeKey]).fileSize) ?? 0
        let ext = file.pathExtension.lowercased()
        let mime = Self.types[ext] ?? UTType(filenameExtension: ext)?.preferredMIMEType ?? "application/octet-stream"
        var headers = ["Content-Type": mime, "Accept-Ranges": "bytes", "Cache-Control": "no-cache"]
        var status = 200, start = 0, end = max(0, size - 1)
        if let header = task.request.value(forHTTPHeaderField: "Range"), let r = Self.range(header, size: size) {
            status = 206; start = r.lowerBound; end = r.upperBound
            headers["Content-Range"] = "bytes \(start)-\(end)/\(size)"
        }
        let length = size == 0 ? 0 : end - start + 1
        headers["Content-Length"] = String(length)
        try? handle.seek(toOffset: UInt64(start))
        let body = (try? handle.read(upToCount: length)) ?? Data()
        respond(task, url: url, status: status, headers: headers, body: body)
    }

    func webView(_ webView: WKWebView, stop task: WKURLSchemeTask) {}

    private func respond(_ task: WKURLSchemeTask, url: URL, status: Int, headers: [String: String], body: Data) {
        guard let r = HTTPURLResponse(url: url, statusCode: status, httpVersion: "HTTP/1.1", headerFields: headers) else { return }
        task.didReceive(r)
        task.didReceive(body)
        task.didFinish()
    }

    /// "bytes=a-b", "bytes=a-" or "bytes=-n"
    static func range(_ header: String, size: Int) -> ClosedRange<Int>? {
        guard size > 0, header.hasPrefix("bytes=") else { return nil }
        let spec = header.dropFirst(6).split(separator: ",").first ?? ""
        let parts = spec.split(separator: "-", omittingEmptySubsequences: false)
        guard parts.count == 2 else { return nil }
        if parts[0].isEmpty, let n = Int(parts[1]), n > 0 { return max(0, size - n)...(size - 1) }
        guard let a = Int(parts[0]), a < size else { return nil }
        let b = min(Int(parts[1]) ?? (size - 1), size - 1)
        return a <= b ? a...b : nil
    }
}
