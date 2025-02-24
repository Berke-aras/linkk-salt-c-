# Link Kısaltma Uygulaması

Bu proje, uzun URL'leri kısaltmak için geliştirilmiş bir web uygulamasıdır. Kullanıcılar, uzun URL'leri daha kısa ve paylaşılabilir hale getirebilirler. Ayrıca, uygulama Papara ile ödeme entegrasyonu ve reklam gösterimleriyle gelir elde etmeyi hedeflemektedir.

## Özellikler

-   **URL Kısaltma**: Kullanıcılar, uzun URL'leri kısaltarak daha kolay paylaşabilirler.
-   **Tema Değiştirme**: Karanlık ve aydınlık tema arasında geçiş yapma imkanı.
-   **Kullanıcı Yönetimi**: Kayıt olma, giriş yapma ve kullanıcıya özel link yönetimi.
-   **Papara Entegrasyonu**: Kullanıcılardan ödeme almak için Papara entegrasyonu.
-   **Reklam Gösterimi**: Uygulama içi reklam alanlarıyla gelir elde etme.
-   **Log Tutma**: Site logları kaydedilir.

## Kurulum

1. **Depoyu Klonlayın**:

    ```bash
    git clone https://github.com/kullaniciadi/link-kisaltma-uygulamasi.git
    cd link-kisaltma-uygulamasi
    ```

2. **Sanal Ortam Oluşturun ve Aktifleştirin**:

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # macOS/Linux
    venv\Scripts\activate  # Windows
    ```

3. **Gereksinimleri Yükleyin**:

    ```bash
    pip install -r requirements.txt
    ```

4. **Veritabanını Oluşturun**:

    ```bash
    flask db init
    flask db migrate -m "Veritabanı oluşturuldu"
    flask db upgrade
    ```

5. **Uygulamayı Başlatın**:

    ```bash
    flask run
    ```

## Papara Entegrasyonu

Uygulama, kullanıcı ödemelerini almak için Papara API'sini kullanır. Entegrasyonu gerçekleştirmek için aşağıdaki adımları izleyin:

1. **Papara API Anahtarını Alın**: [Papara İş Ortağı Portalı](https://merchant.papara.com/) üzerinden API anahtarınızı edinin.

2. **Yapılandırma Dosyasını Güncelleyin**: `config.py` dosyasına aşağıdaki satırları ekleyin:

    ```python
    PAPARA_API_KEY = 'Sizin_Papara_API_Anahtarınız'
    ```

3. **Ödeme İşlemlerini Ekleyin**: `payments.py` dosyasında Papara API'si ile ödeme işlemlerini yönetin. Örnek bir istek:

    ```python
    import requests

    def create_papara_payment(amount, user_id):
        url = 'https://api.papara.com/payments'
        headers = {
            'Authorization': f'Bearer {PAPARA_API_KEY}',
            'Content-Type': 'application/json'
        }
        data = {
            'amount': amount,
            'userId': user_id,
            'redirectUrl': 'https://siteniz.com/odeme/basarili',
            'failUrl': 'https://siteniz.com/odeme/basarisiz'
        }
        response = requests.post(url, headers=headers, json=data)
        return response.json()
    ```

## Reklam Entegrasyonu

Uygulama, gelir elde etmek için reklam alanları içerir. Reklam entegrasyonu için aşağıdaki adımları izleyin:

1. **Reklam Sağlayıcınızı Seçin**: Google AdSense, PropellerAds veya diğer reklam ağlarını kullanabilirsiniz.

2. **Reklam Kodlarını Ekleyin**: `templates/layout.html` dosyasında uygun yerlere reklam kodlarını yerleştirin. Örneğin:

    ```html
    <div class="ad">
        <!-- Reklam Kodu Başlangıcı -->
        <script src="https://ads.reklamagi.com/ad.js"></script>
        <!-- Reklam Kodu Bitişi -->
    </div>
    ```

3. **Reklam Alanlarını Stilize Edin**: `static/styles.css` dosyasında reklam alanlarının görünümünü düzenleyin.

    ```css
    .ad {
        margin: 20px 0;
        text-align: center;
    }
    ```

## Katkıda Bulunma

Katkılarınızı bekliyoruz! Lütfen katkıda bulunmak için bir `fork` yapın, kendi dalınızı oluşturun, değişikliklerinizi yapın ve bir `pull request` gönderin.

1. **Depoyu Forklayın**
2. **Özellik Dalınızı Oluşturun** (`git checkout -b ozellik/YeniOzellik`)
3. **Değişikliklerinizi Kaydedin** (`git commit -am 'Yeni özellik eklendi'`)
4. **Dalı Gönderin** (`git push origin ozellik/YeniOzellik`)
5. **Bir Pull Request Oluşturun**

## Lisans

Bu proje MIT Lisansı ile lisanslanmıştır. Daha fazla bilgi için `LICENSE` dosyasına bakın.
