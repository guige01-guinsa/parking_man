package com.parkingmanagement.app;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.provider.Settings;
import android.webkit.CookieManager;
import android.webkit.JavascriptInterface;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;

import com.android.billingclient.api.BillingClient;
import com.android.billingclient.api.BillingClientStateListener;
import com.android.billingclient.api.BillingFlowParams;
import com.android.billingclient.api.BillingResult;
import com.android.billingclient.api.PendingPurchasesParams;
import com.android.billingclient.api.ProductDetails;
import com.android.billingclient.api.Purchase;
import com.android.billingclient.api.PurchasesUpdatedListener;
import com.android.billingclient.api.QueryProductDetailsParams;
import com.android.billingclient.api.QueryPurchasesParams;

import org.json.JSONObject;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

public class MainActivity extends Activity implements PurchasesUpdatedListener {
    private static final int FILE_CHOOSER_REQUEST = 5101;

    private WebView webView;
    private BillingClient billingClient;
    private ValueCallback<Uri[]> filePathCallback;
    private final Map<String, ProductDetails> productDetailsById = new HashMap<>();

    private final String[] subscriptionProductIds = new String[] {
        BuildConfig.STARTER_PRODUCT_ID,
        BuildConfig.STANDARD_PRODUCT_ID,
        BuildConfig.PRO_PRODUCT_ID
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        webView = new WebView(this);
        setContentView(webView);
        configureWebView();
        configureBilling();
        webView.loadUrl(BuildConfig.APP_URL);
    }

    private void configureWebView() {
        CookieManager.getInstance().setAcceptCookie(true);
        CookieManager.getInstance().setAcceptThirdPartyCookies(webView, false);

        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setMediaPlaybackRequiresUserGesture(false);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(true);

        webView.addJavascriptInterface(new BillingBridge(), "ParkingBilling");
        webView.setWebViewClient(new WebViewClient());
        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onShowFileChooser(
                WebView view,
                ValueCallback<Uri[]> filePath,
                FileChooserParams fileChooserParams
            ) {
                if (filePathCallback != null) {
                    filePathCallback.onReceiveValue(null);
                }
                filePathCallback = filePath;
                try {
                    startActivityForResult(fileChooserParams.createIntent(), FILE_CHOOSER_REQUEST);
                } catch (Exception exc) {
                    filePathCallback = null;
                    toast("파일 선택 앱을 열 수 없습니다.");
                    return false;
                }
                return true;
            }
        });
    }

    private void configureBilling() {
        billingClient = BillingClient.newBuilder(this)
            .setListener(this)
            .enableAutoServiceReconnection()
            .enablePendingPurchases(PendingPurchasesParams.newBuilder().enableOneTimeProducts().build())
            .build();
        connectBilling();
    }

    private void connectBilling() {
        if (billingClient == null || billingClient.isReady()) {
            return;
        }
        billingClient.startConnection(new BillingClientStateListener() {
            @Override
            public void onBillingSetupFinished(BillingResult billingResult) {
                if (billingResult.getResponseCode() == BillingClient.BillingResponseCode.OK) {
                    queryProducts();
                    queryExistingPurchases();
                } else {
                    notifyBillingError("Google Play 결제 연결 실패: " + billingResult.getDebugMessage());
                }
            }

            @Override
            public void onBillingServiceDisconnected() {
                productDetailsById.clear();
            }
        });
    }

    private void queryProducts() {
        List<QueryProductDetailsParams.Product> products = new ArrayList<>();
        for (String productId : subscriptionProductIds) {
            products.add(
                QueryProductDetailsParams.Product.newBuilder()
                    .setProductId(productId)
                    .setProductType(BillingClient.ProductType.SUBS)
                    .build()
            );
        }

        QueryProductDetailsParams params = QueryProductDetailsParams.newBuilder()
            .setProductList(products)
            .build();

        billingClient.queryProductDetailsAsync(params, (billingResult, productDetailsResult) -> {
            if (billingResult.getResponseCode() != BillingClient.BillingResponseCode.OK) {
                notifyBillingError("구독 상품 조회 실패: " + billingResult.getDebugMessage());
                return;
            }
            productDetailsById.clear();
            for (ProductDetails details : productDetailsResult.getProductDetailsList()) {
                productDetailsById.put(details.getProductId(), details);
            }
        });
    }

    private void queryExistingPurchases() {
        if (billingClient == null || !billingClient.isReady()) {
            return;
        }
        QueryPurchasesParams params = QueryPurchasesParams.newBuilder()
            .setProductType(BillingClient.ProductType.SUBS)
            .build();
        billingClient.queryPurchasesAsync(params, (billingResult, purchases) -> {
            if (billingResult.getResponseCode() != BillingClient.BillingResponseCode.OK) {
                return;
            }
            for (Purchase purchase : purchases) {
                handlePurchase(purchase);
            }
        });
    }

    private void launchPurchase(String productId, String accountHint) {
        if (billingClient == null || !billingClient.isReady()) {
            connectBilling();
            toast("Google Play 결제 연결 중입니다. 잠시 후 다시 눌러 주세요.");
            return;
        }
        ProductDetails productDetails = productDetailsById.get(productId);
        if (productDetails == null) {
            queryProducts();
            toast("구독 상품 정보를 불러오는 중입니다. 잠시 후 다시 눌러 주세요.");
            return;
        }

        String offerToken = firstOfferToken(productDetails);
        if (offerToken == null) {
            notifyBillingError("구독 기본 혜택이 설정되지 않았습니다.");
            return;
        }

        List<BillingFlowParams.ProductDetailsParams> productParamsList = new ArrayList<>();
        productParamsList.add(
            BillingFlowParams.ProductDetailsParams.newBuilder()
                .setProductDetails(productDetails)
                .setOfferToken(offerToken)
                .build()
        );

        BillingFlowParams.Builder flowBuilder = BillingFlowParams.newBuilder()
            .setProductDetailsParamsList(productParamsList);
        String obfuscatedAccountId = obfuscatedAccountId(accountHint);
        if (obfuscatedAccountId != null) {
            flowBuilder.setObfuscatedAccountId(obfuscatedAccountId);
        }
        BillingResult result = billingClient.launchBillingFlow(this, flowBuilder.build());
        if (result.getResponseCode() != BillingClient.BillingResponseCode.OK) {
            notifyBillingError("구독 화면을 열 수 없습니다: " + result.getDebugMessage());
        }
    }

    private String firstOfferToken(ProductDetails productDetails) {
        List<ProductDetails.SubscriptionOfferDetails> offerDetails = productDetails.getSubscriptionOfferDetails();
        if (offerDetails == null || offerDetails.isEmpty()) {
            return null;
        }
        return offerDetails.get(0).getOfferToken();
    }

    @Override
    public void onPurchasesUpdated(BillingResult billingResult, List<Purchase> purchases) {
        int responseCode = billingResult.getResponseCode();
        if (responseCode == BillingClient.BillingResponseCode.OK && purchases != null) {
            for (Purchase purchase : purchases) {
                handlePurchase(purchase);
            }
            return;
        }
        if (responseCode == BillingClient.BillingResponseCode.USER_CANCELED) {
            toast("구독이 취소되었습니다.");
            return;
        }
        notifyBillingError("구독 처리 실패: " + billingResult.getDebugMessage());
    }

    private void handlePurchase(Purchase purchase) {
        if (purchase.getPurchaseState() != Purchase.PurchaseState.PURCHASED) {
            return;
        }
        List<String> products = purchase.getProducts();
        if (products == null || products.isEmpty()) {
            return;
        }
        String productId = products.get(0);
        notifyPurchaseToWeb(productId, purchase.getPurchaseToken());
    }

    private void notifyPurchaseToWeb(String productId, String purchaseToken) {
        String script = String.format(
            Locale.US,
            "window.handleParkingPlayPurchase && window.handleParkingPlayPurchase(%s,%s);",
            JSONObject.quote(productId),
            JSONObject.quote(purchaseToken)
        );
        runOnUiThread(() -> webView.evaluateJavascript(script, null));
    }

    private void notifyBillingError(String message) {
        String script = String.format(
            Locale.US,
            "window.handleParkingPlayBillingError && window.handleParkingPlayBillingError(%s);",
            JSONObject.quote(message)
        );
        runOnUiThread(() -> webView.evaluateJavascript(script, null));
    }

    private String obfuscatedAccountId(String accountHint) {
        String source = accountHint == null || accountHint.trim().isEmpty()
            ? Settings.Secure.getString(getContentResolver(), Settings.Secure.ANDROID_ID)
            : accountHint.trim();
        if (source == null || source.isEmpty()) {
            return null;
        }
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(source.getBytes(StandardCharsets.UTF_8));
            StringBuilder result = new StringBuilder();
            for (byte b : hash) {
                result.append(String.format(Locale.US, "%02x", b));
            }
            return result.substring(0, Math.min(result.length(), 64));
        } catch (Exception exc) {
            return null;
        }
    }

    private void toast(String message) {
        runOnUiThread(() -> Toast.makeText(this, message, Toast.LENGTH_SHORT).show());
    }

    @Override
    protected void onResume() {
        super.onResume();
        queryExistingPurchases();
    }

    @Override
    protected void onDestroy() {
        if (billingClient != null) {
            billingClient.endConnection();
        }
        if (webView != null) {
            webView.destroy();
        }
        super.onDestroy();
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != FILE_CHOOSER_REQUEST || filePathCallback == null) {
            return;
        }
        Uri[] results = WebChromeClient.FileChooserParams.parseResult(resultCode, data);
        filePathCallback.onReceiveValue(results);
        filePathCallback = null;
    }

    public class BillingBridge {
        @JavascriptInterface
        public void purchase(String productId) {
            purchase(productId, "");
        }

        @JavascriptInterface
        public void purchase(String productId, String accountHint) {
            runOnUiThread(() -> launchPurchase(productId, accountHint));
        }
    }
}
