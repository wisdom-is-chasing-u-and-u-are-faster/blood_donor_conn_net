import UIKit
import WebKit

@main
class AppDelegate: UIResponder, UIApplicationDelegate {
    var window: UIWindow?

    func application(_ application: UIApplication, didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
        window = UIWindow(frame: UIScreen.main.bounds)
        let viewController = UIViewController()
        let webView = WKWebView(frame: viewController.view.bounds)
        if let url = URL(string: "https://blood-donor-network.run.app") {
            webView.load(URLRequest(url: url))
        }
        viewController.view.addSubview(webView)
        window?.rootViewController = viewController
        window?.makeKeyAndVisible()
        return true
    }
}
