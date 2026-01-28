# Waarom heeft de Cursor-terminal geen internet?

## Oorzaak

Cursor voert commando’s die de AI aanroept standaard uit in een **sandbox** met:
- **Netwerk: uit** (geblokkeerd)
- Schrijven alleen in je workspace
- Geen toegang buiten de workspace

Daardoor zie je:
- `ConnectionRefusedError [WinError 10061]` of “Kan geen verbinding maken”
- `SANDBOXING: Network access: Blocked` onderaan de output
- Pip kan PyPI niet bereiken → “Could not find a version that satisfies the requirement … (from versions: none)”

Jouw PC heeft wel internet; het *proces* waarin het commando draait, krijgt in die sandbox geen netwerk.

(Bron: [Cursor Docs – Terminal](https://cursor.com/docs/agent/terminal): “By default, Agent runs terminal commands in a restricted environment that blocks … network activity” en “Network access: Blocked by default (**configurable in settings**)”.)

## Oplossing: netwerk aanzetten voor de sandbox

1. Open **Cursor Settings**: `Ctrl+,` of **File → Preferences → Cursor Settings**.
2. Ga naar **Agents → Auto-Run**.
3. Zet **Auto-Run Network Access** aan (zodat commando’s in de sandbox wél netwerk krijgen).

Daarna zouden o.a. `pip install` en je hercategoriseerscript vanaf de Cursor-terminal weer moeten werken.

## Alternatief

- **Run** of **Add to allowlist** kiezen wanneer Cursor vraagt om een geblokkeerd commando (dan loopt dat commando buiten de sandbox, mét netwerk).
- Het script in een **eigen terminal** (buiten Cursor) draaien; daar is netwerk normaal altijd beschikbaar.
