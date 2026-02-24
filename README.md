# CSV Cift Tirnak Temizleyici (Streamlit)

Bu uygulama CSV dosyalarinin icindeki cift tirnak (`"`) karakterlerini hucrelerden kaldirir.

## Lokal Calistirma

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Cloud Deploy

1. Bu projeyi GitHub'a yukle
2. Streamlit Cloud -> New App
3. Repo sec -> `app.py` sec -> Deploy

## Kullanim

- **CSV dosyalari yukle (coklu):** Her CSV icin `modified_<ad>.csv` uretir.
- **CSV iceren ZIP yukle:** ZIP icindeki tum CSV'leri (alt klasorler dahil) isler ve ciktilari ayni klasor yapisiyla ZIP'e koyar.
