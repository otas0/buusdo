# Guida utente buusdo (Italiano)

Lingue: [English](en.md) · [简体中文](zh.md) · [繁體中文](zh-Hant.md) · [日本語](ja.md) · [한국어](ko.md) · [Português (Brasil)](pt-BR.md) · [Português](pt.md) · [Español](es.md) · [Deutsch](de.md) · [Français](fr.md) · **Italiano** · [Русский](ru.md)

Download e avvio su Windows, macOS e Linux. [v1.0.0](https://github.com/otas0/buusdo/releases/tag/v1.0.0).

## Panoramica

Scheduler / coordinatore di configurazione grafica. Kit BYO. macOS è **solo config**. v1.0.0 è **non firmato**.

## 1. Download

Su [https://github.com/otas0/buusdo/releases/tag/v1.0.0](https://github.com/otas0/buusdo/releases/tag/v1.0.0) → **Assets**: Setup Windows `.exe` / zip macOS `.app` / Linux onedir o wheel + `install_linux.sh`.

## 2. Windows

1. Esplora file → **Download** → tasto destro `.exe` → **Proprietà** → spunta **Sblocca** → **Applica** → **OK**.
2. Doppio clic. Se compare **Windows ha protetto il PC**: **Ulteriori informazioni** → **Esegui comunque**. UAC: **Sì**.
3. Dopo l’installazione: tasto Win, digita `buusdo`.
4. File sparito: **Sicurezza di Windows** → **Protezione da virus** → **Cronologia** → **Ripristina**.

Python non serve per il Setup.

## 3. macOS

1. Estrai lo zip; trascina `Buusdo.app` in **Applicazioni**.
2. **Clic destro** → **Apri** → di nuovo **Apri**.
3. Non solo doppio clic; non disattivare SIP.
4. **Impostazioni di Sistema** → **Privacy e sicurezza** → **Apri comunque**.

## 4. Linux

```bash
bash install_linux.sh && buusdo
python3 -m pip install ./buusdo-*-py3-none-any.whl "PySide6-Essentials==6.12.0" && python3 -m buusdo
```

## 5. Dopo il primo avvio

Seleziona le cartelle kit nell’UI. Nessun bypass anti-cheat. Issues: https://github.com/otas0/buusdo/issues.

---

## Related docs

- Signing status: [CODE_SIGNING.md](../CODE_SIGNING.md)
- macOS package notes: [MAC_PACKAGE.md](../MAC_PACKAGE.md)
- Hardware honesty: [HARDWARE_NOTES.md](../HARDWARE_NOTES.md)
- Project constraints: [PROJECT.md](../PROJECT.md)

v1.0.0 is **unsigned**. SmartScreen / Gatekeeper warnings are expected. You do **not** need a system Python install to run the Windows Setup or macOS `.app` packages.

*[English](en.md) · [简体中文](zh.md) · [繁體中文](zh-Hant.md) · [日本語](ja.md) · [한국어](ko.md) · [Português (Brasil)](pt-BR.md) · [Português](pt.md) · [Español](es.md) · [Deutsch](de.md) · [Français](fr.md) · **Italiano** · [Русский](ru.md)*
