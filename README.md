# 🧩 Supaprastinta blokų grandinė – v0.2

**Indėlis:**  
- **Valentinas Šamatovičius** – vartotojų, transakcijų ir blokų kūrimas, individualaus hash algoritmo integravimas, balansų atnaujinimas, lygiagretus kasimas (parallel mining), „Proof-of-Work“ kasimo logika.  
- **Adrius Rakauskas** – Merkle medžio (Merkle Tree) įgyvendinimas, „Proof-of-Work“ kasimo logika, blokų patikrinimo (verification) logika, papildomos validacijos funkcijos, UTXO modelis

---

## 🧱 Projekto aprašymas

Šis projektas sukurtas siekiant praktiškai pavaizduoti, kaip veikia supaprastinta blokų grandinės sistema.  
Sistema imituoja pagrindinius „blockchain“ technologijos veikimo principus: transakcijų kūrimą, blokų formavimą, kriptografinį maišymą (hash), darbo įrodymo algoritmą (Proof-of-Work), kasėjų (miners) konkurenciją bei blokų grandinės validaciją.

Projekto tikslas – sukurti veikiančią decentralizuotos sistemos modelį, kuriame kiekvienas blokas būtų patikimas, tikrinamas ir susietas su ankstesniu.

---
## 📂 Projekto struktūra

```plaintext
Blockchain2/
│
├── user.py              # Vartotojų kūrimas, vieši/privatūs raktai, balansų atnaujinimas
├── transaction.py       # Transakcijų kūrimas, ID generavimas ir hash skaičiavimas
├── block.py             # Vieno bloko duomenys, maišos skaičiavimas, Merkle root (v0.2)
├── blockchain.py        # Pagrindinė blockchain logika, kasimo algoritmas (Proof-of-Work)
├── custom_hash.py       # Individualus hash algoritmas (konvertuotas iš C++)
├── data_gen.py          # Testinių vartotojų ir transakcijų generavimas
├── main.py              # Pagrindinis paleidimo failas (simuliacija ir testavimas)
└── README_v0_2.md       # Projekto dokumentacija



```
---
## 🧩 Projekto eiga

###  Versija v0.1 – pagrindinė struktūra

**Įgyvendinta:**
- Sukurta klasė `User` (vartotojas) su unikaliu vardu, viešu raktu (`public_key`) ir pradiniu balansu.  
- Sukurta klasė `Transaction`, generuojanti siuntėjo ir gavėjo transakcijas bei `tx_id` (naudojant `custom_hash256`).  
- Sukurta klasė `Block`, kurioje talpinamas transakcijų sąrašas, `prev_hash`, `nonce` ir bloko hash.  
- Sukurta klasė `Blockchain`, leidžianti jungti blokus į grandinę.  
- Integruotas individualus hash algoritmas (`custom_hash256`) iš C++ kodo.  

**Rezultatas:**  
Veikianti sistema, galinti sukurti vartotojus, generuoti transakcijas, jungti juos į blokus ir saugoti grandinėje, tačiau dar be kasimo (mining) logikos.

---

### 🟡 Versija v0.2 – išplėstinė blokų grandinė

**Patobulinta:**

- Įdiegta **lygiagretaus kasimo (Parallel Mining)** simuliacija – keli kasėjai vienu metu ieško tinkamo `nonce`.  
- Pridėtas **kasimo laiko limitas (`mining_time_limit`)** – kasėjai dirba tik tam tikrą laiko tarpą.  
- Įgyvendinta **kasėjų atranka ir atlygis** – 50 monetų + galimi mokesčiai už transakcijas.  
- Patobulinta **Proof-of-Work** – dabar keli kasėjai konkuruoja dėl pirmojo tinkamo hash su nulių prefiksu.  
- Įdiegta **transakcijų validacija** – tikrinama, ar siuntėjo balansas pakankamas; neteisingos transakcijos praleidžiamos.  
- Pridėtas **Merkle Tree (Merkle medis)** – kiekvieno bloko transakcijų ID sujungiami į vieną šaknies hash (`merkle_root`), kuris saugomas bloko antraštėje.  
- Įgyvendintas **blokų patikrinimas (Verification)** – tikrinamas `merkle_root`, `prev_hash` ir PoW teisingumas.  
- Automatinis **genesis bloko** kūrimas su 64 nuliais kaip `prev_hash`.  
- Patobulinta **grandinių validacija**, tikrinanti visų blokų nuoseklumą ir PoW.  
- Pagrindinė simuliacija per `main.py`, valdant baseiną (`tx_pool`) ir kasėjų veiklą.  

**Rezultatas:**  
Visiškai funkcionuojanti, decentralizuota blokų grandinės sistema su keliais kasėjais, Proof-of-Work, Merkle medžiu, blokų validacija ir balansų atnaujinimu.

### Veikimo/paleidimo pavyzdžiai
sita tau palieku garbe

### Naudojimosi instrukcija
tau irgi

### Išvados
all u

