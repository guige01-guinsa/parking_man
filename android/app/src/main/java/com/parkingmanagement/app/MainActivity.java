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
import com.google.mlkit.vision.common.InputImage;
import com.google.mlkit.vision.text.Text;
import com.google.mlkit.vision.text.TextRecognition;
import com.google.mlkit.vision.text.TextRecognizer;
import com.google.mlkit.vision.text.korean.KoreanTextRecognizerOptions;
import com.google.mlkit.vision.text.latin.TextRecognizerOptions;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class MainActivity extends Activity implements PurchasesUpdatedListener {
    private static final int FILE_CHOOSER_REQUEST = 5101;
    private static final String PLATE_MIDDLE_CHARS = "가나다라마바사아자거너더러머버서어저고노도로모보소오조구누두루무부수우주바사자배허하호";
    private static final Pattern PLATE_PATTERN = Pattern.compile("\\d{2,3}[" + PLATE_MIDDLE_CHARS + "]\\d{4}");

    private WebView webView;
    private BillingClient billingClient;
    private TextRecognizer koreanTextRecognizer;
    private TextRecognizer latinTextRecognizer;
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
        configureOcr();
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
        webView.addJavascriptInterface(new NativeOcrBridge(), "ParkingNativeOcr");
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

    private void configureOcr() {
        koreanTextRecognizer = TextRecognition.getClient(new KoreanTextRecognizerOptions.Builder().build());
        latinTextRecognizer = TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS);
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

    private void notifyNativeOcr(JSONObject payload) {
        String script = String.format(
            Locale.US,
            "window.handleNativePlateOcr && window.handleNativePlateOcr(%s);",
            payload.toString()
        );
        runOnUiThread(() -> webView.evaluateJavascript(script, null));
    }

    private void notifyNativeOcrError(String message) {
        try {
            JSONObject payload = new JSONObject();
            payload.put("provider", "android-mlkit");
            payload.put("raw_text", "");
            payload.put("candidates", new JSONArray());
            payload.put("error", message);
            notifyNativeOcr(payload);
        } catch (Exception ignored) {
            // ignore
        }
    }

    private void runNativeOcr(Uri imageUri) {
        if (imageUri == null || koreanTextRecognizer == null || latinTextRecognizer == null) {
            return;
        }
        final long startedAt = System.currentTimeMillis();
        final InputImage image;
        try {
            image = InputImage.fromFilePath(this, imageUri);
        } catch (IOException exc) {
            notifyNativeOcrError("휴대폰 OCR 이미지를 읽지 못했습니다.");
            return;
        }

        koreanTextRecognizer.process(image)
            .addOnSuccessListener(koreanText -> latinTextRecognizer.process(image)
                .addOnSuccessListener(latinText -> publishNativeOcr(koreanText, latinText, startedAt))
                .addOnFailureListener(exc -> publishNativeOcr(koreanText, null, startedAt)))
            .addOnFailureListener(exc -> latinTextRecognizer.process(image)
                .addOnSuccessListener(latinText -> publishNativeOcr(null, latinText, startedAt))
                .addOnFailureListener(fallbackExc -> notifyNativeOcrError("휴대폰 OCR 판독에 실패했습니다.")));
    }

    private void publishNativeOcr(Text koreanText, Text latinText, long startedAt) {
        StringBuilder rawTextBuilder = new StringBuilder();
        if (koreanText != null && !koreanText.getText().trim().isEmpty()) {
            rawTextBuilder.append("[android-korean] ").append(koreanText.getText().trim());
        }
        if (latinText != null && !latinText.getText().trim().isEmpty()) {
            if (rawTextBuilder.length() > 0) {
                rawTextBuilder.append("\n");
            }
            rawTextBuilder.append("[android-latin] ").append(latinText.getText().trim());
        }

        String rawText = rawTextBuilder.toString().trim();
        List<String> candidates = extractPlateCandidates(rawText);
        try {
            JSONObject payload = new JSONObject();
            JSONArray candidateArray = new JSONArray();
            for (String candidate : candidates) {
                candidateArray.put(candidate);
            }
            payload.put("provider", "android-mlkit");
            payload.put("raw_text", rawText);
            payload.put("candidates", candidateArray);
            payload.put("elapsed_ms", Math.max(0, System.currentTimeMillis() - startedAt));
            notifyNativeOcr(payload);
        } catch (Exception exc) {
            notifyNativeOcrError("휴대폰 OCR 결과를 전달하지 못했습니다.");
        }
    }

    private List<String> extractPlateCandidates(String text) {
        Set<String> candidates = new LinkedHashSet<>();
        List<String> variants = new ArrayList<>();
        variants.add(text == null ? "" : text);
        variants.add((text == null ? "" : text).replaceAll("\\s+", ""));
        variants.add((text == null ? "" : text).replaceAll("[\\s\\-_/.:]", ""));

        for (String variant : variants) {
            String compact = compactPlateText(variant);
            Matcher matcher = PLATE_PATTERN.matcher(compact);
            while (matcher.find()) {
                candidates.add(matcher.group());
            }
            for (int windowSize : new int[] {7, 8}) {
                if (compact.length() < windowSize) {
                    continue;
                }
                for (int index = 0; index <= compact.length() - windowSize; index++) {
                    String repaired = repairPlateWindow(compact.substring(index, index + windowSize));
                    if (repaired != null) {
                        candidates.add(repaired);
                    }
                }
            }
        }
        return new ArrayList<>(candidates);
    }

    private String compactPlateText(String text) {
        if (text == null) {
            return "";
        }
        return text.trim()
            .toUpperCase(Locale.US)
            .replaceAll("[\\s\\-_/.:]", "")
            .replaceAll("[^0-9A-Z가-힣|!$]", "");
    }

    private String repairPlateWindow(String window) {
        int middleIndex = window.length() - 5;
        if (middleIndex != 2 && middleIndex != 3) {
            return null;
        }
        char middle = window.charAt(middleIndex);
        if (PLATE_MIDDLE_CHARS.indexOf(middle) < 0) {
            return null;
        }
        String head = repairDigits(window.substring(0, middleIndex));
        String tail = repairDigits(window.substring(middleIndex + 1));
        if (head == null || tail == null) {
            return null;
        }
        String candidate = head + middle + tail;
        return PLATE_PATTERN.matcher(candidate).matches() ? candidate : null;
    }

    private String repairDigits(String value) {
        StringBuilder digits = new StringBuilder();
        for (int i = 0; i < value.length(); i++) {
            char item = value.charAt(i);
            if (Character.isDigit(item)) {
                digits.append(item);
                continue;
            }
            String mapped = similarDigit(item);
            if (mapped == null) {
                return null;
            }
            digits.append(mapped);
        }
        return digits.toString();
    }

    private String similarDigit(char value) {
        switch (value) {
            case 'O':
            case 'Q':
            case 'D':
            case 'U':
                return "0";
            case 'I':
            case 'L':
            case '|':
            case '!':
                return "1";
            case 'Z':
                return "2";
            case 'A':
                return "4";
            case 'S':
            case '$':
                return "5";
            case 'G':
                return "6";
            case 'T':
                return "7";
            case 'B':
                return "8";
            default:
                return null;
        }
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
        if (koreanTextRecognizer != null) {
            koreanTextRecognizer.close();
        }
        if (latinTextRecognizer != null) {
            latinTextRecognizer.close();
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
        if (results != null && results.length > 0) {
            runNativeOcr(results[0]);
        }
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

    public class NativeOcrBridge {
        @JavascriptInterface
        public boolean isAvailable() {
            return koreanTextRecognizer != null && latinTextRecognizer != null;
        }
    }
}
