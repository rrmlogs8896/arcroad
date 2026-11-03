import SwiftUI
import WebKit

/// One page of the bundled site, shown without the website's own header and menu (the app's tabs replace them).
struct WebScreen: UIViewRepresentable {
    let path: String

    func makeCoordinator() -> Coordinator { Coordinator() }

    func makeUIView(context: Context) -> WKWebView {
        let cfg = WKWebViewConfiguration()
        cfg.setURLSchemeHandler(SiteSchemeHandler(), forURLScheme: Site.scheme)
        cfg.allowsInlineMediaPlayback = true
        cfg.mediaTypesRequiringUserActionForPlayback = []
        let css = "header, .staging, nav.sn { display: none !important; } html { -webkit-tap-highlight-color: transparent; }"
        let js = "document.documentElement.classList.add('in-app'); var s = document.createElement('style'); s.textContent = '\(css)'; document.documentElement.appendChild(s);"
        cfg.userContentController.addUserScript(WKUserScript(source: js, injectionTime: .atDocumentStart, forMainFrameOnly: true))

        let view = WKWebView(frame: .zero, configuration: cfg)
        view.navigationDelegate = context.coordinator
        view.allowsBackForwardNavigationGestures = true
        view.isOpaque = false
        view.backgroundColor = UIColor(Palette.bg)
        view.scrollView.backgroundColor = UIColor(Palette.bg)
        view.load(URLRequest(url: Site.url(path)))
        return view
    }

    func updateUIView(_ view: WKWebView, context: Context) {}

    final class Coordinator: NSObject, WKNavigationDelegate {
        /// Pages in the app stay in the app; anything else (a source, a map, mail) opens outside it.
        func webView(_ webView: WKWebView, decidePolicyFor action: WKNavigationAction,
                     decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
            guard let url = action.request.url, let scheme = url.scheme?.lowercased() else { decisionHandler(.cancel); return }
            if [Site.scheme, "about", "blob", "data"].contains(scheme) { decisionHandler(.allow); return }
            if action.targetFrame != nil && action.targetFrame?.isMainFrame == false { decisionHandler(.allow); return }
            UIApplication.shared.open(url)
            decisionHandler(.cancel)
        }
    }
}
