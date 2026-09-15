import AVFoundation
import SwiftUI
import UIKit
import WebKit

@main
struct LingtaiMirrorApp: App {
    var body: some Scene {
        WindowGroup {
            LingtaiWebView()
                .ignoresSafeArea(.container, edges: [.top, .bottom])
                .preferredColorScheme(.dark)
        }
    }
}

struct LingtaiWebView: UIViewRepresentable {
    func makeCoordinator() -> Coordinator { Coordinator() }

    func makeUIView(context: Context) -> WKWebView {
        let configuration = WKWebViewConfiguration()
        configuration.allowsInlineMediaPlayback = true
        configuration.mediaTypesRequiringUserActionForPlayback = []
        configuration.defaultWebpagePreferences.allowsContentJavaScript = true
        activatePlaybackSession()

        let webView = WKWebView(frame: .zero, configuration: configuration)
        webView.backgroundColor = UIColor(red: 0.086, green: 0.067, blue: 0.055, alpha: 1)
        webView.isOpaque = true
        webView.scrollView.contentInsetAdjustmentBehavior = .never
        webView.navigationDelegate = context.coordinator
        webView.uiDelegate = context.coordinator
        webView.allowsBackForwardNavigationGestures = true

        let root = Bundle.main.resourceURL!.appendingPathComponent("WebContent", isDirectory: true)
        let index = root.appendingPathComponent("index.html")
        webView.loadFileURL(index, allowingReadAccessTo: root)
        return webView
    }

    func updateUIView(_ webView: WKWebView, context: Context) {}

    private func activatePlaybackSession() {
        let session = AVAudioSession.sharedInstance()
        do {
            try session.setCategory(.playback, mode: .spokenAudio, options: [])
            try session.setActive(true)
        } catch {}
    }

    final class Coordinator: NSObject, WKNavigationDelegate, WKUIDelegate {
        func webView(_ webView: WKWebView, decidePolicyFor navigationAction: WKNavigationAction,
                     decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
            guard let url = navigationAction.request.url else {
                decisionHandler(.cancel)
                return
            }

            if url.isFileURL || url.host == "emituofo.fun" || url.host == "www.emituofo.fun" {
                decisionHandler(.allow)
            } else if ["http", "https", "mailto"].contains(url.scheme?.lowercased() ?? "") {
                UIApplication.shared.open(url)
                decisionHandler(.cancel)
            } else {
                decisionHandler(.cancel)
            }
        }

        func webView(_ webView: WKWebView, createWebViewWith configuration: WKWebViewConfiguration,
                     for navigationAction: WKNavigationAction, windowFeatures: WKWindowFeatures) -> WKWebView? {
            if let url = navigationAction.request.url {
                if url.isFileURL {
                    webView.load(navigationAction.request)
                } else {
                    UIApplication.shared.open(url)
                }
            }
            return nil
        }
    }
}
