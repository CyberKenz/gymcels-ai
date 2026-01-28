import os
import io
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash, get_flashed_messages, send_file
from dotenv import load_dotenv
from groq import Groq
from datetime import datetime
import re

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

AI_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key = AI_KEY)

def panggilAi(prompt):
    try:
        chatCompletion = client.chat.completions.create(
            messages= [
                {
                    "role" : "user",
                    "content" : f"""Instruksi: Instruksi: Untuk teks di dalam kurung kurawal {prompt} keluarkan **HANYA** jawaban akhir yang siap-pakai. 
                                Jangan sertakan penjelasan, langkah, alasan, atau teks tambahan apa pun. Jika jawaban berupa angka/rumus/kode, tampilkan langsung dalam format dapat dijalankan. 
                                Jawaban harus sesingkat mungkin untuk menghemat token tapi harus jelas dan sesuai instruksi yang di berikan.
                                Pertanyaan: {prompt}"""
                }
            ],
            model = "openai/gpt-oss-120b",
            stream = False,
        )
        aiOutput = chatCompletion.choices[0].message.content
        return aiOutput
    except Exception:
        return "Fitur AI Sedang Bermasalah!"


@app.route("/")
def home():
    judulWeb = "Gymcels AI"
    return render_template("home.html", webTitle = judulWeb)

@app.route("/cekKalori", methods=['GET', 'POST'])
def cekKalori():
    errors = {}
    inputUser = {}
    suksess = None

    if(request.method == 'POST'):
        gender = request.form.get('gender', '').strip().lower()
        beratBadan = request.form.get('bb', '').strip()
        tinggiBadan = request.form.get('tb', '').strip()
        aktivitas = request.form.get('aktivitas', '').strip()

        inputUser = {
            'gender' : gender,
            'bb' : beratBadan,
            'tb' : tinggiBadan,
            'aktv' : aktivitas
        }

        if not gender:
            errors['gender'] = "Inputan gender tidak boleh kosong!"

        if not beratBadan:
            errors['bb'] = "Inputan berat badan tidak boleh kosong!"
        else:
            try:
                bb = float(beratBadan)
                if bb <= 10:
                    errors['bb'] = "Inputan berat badan minimal harus di atas 10kg!"
            except ValueError:
                errors['bb'] = "Inputan berat badan harus berupa angka (contoh: 65)."

        if not tinggiBadan:
            errors['tb'] = "Inputan tinggi badan tidak boleh kosong!"
        else:
            try:
                tb = float(tinggiBadan)
                if tb <= 50:
                    errors['tb'] = "Inputan tinggi badan minimal harus di atas 50cm!"
            except ValueError:
                errors['tb'] = "Inputan tinggi badan harus berupa angka (contoh: 180)."

        if not aktivitas:
            errors['aktv'] = "Inputan aktivitas tidak boleh kosong!"
        else:
            try:
                aktv = int(aktivitas)
                if not (0 <= aktv <= 7):
                    errors['aktv'] = "Inputan aktivitas tidak boleh kurang dari 0 dan lebih dari 7!"
            except ValueError:
                errors['aktv'] = "Inputan aktivitas harus berupa angka bulat (0 sampai 7)."

        prompt = f"""Tolong hitungkan kalori untuk {gender},dengan berat badan {bb}kg, tinggi {tb}cm, dan aktivitas olahraga/gym {aktv}x/minggu. 
                    Gunakan Mifflin-St Jeor:
                    BMR pria = 10×bb + 6.25×tb − 5×age + 5;
                    BMR wanita = 10×bb + 6.25×tb − 5×age − 161.
                    Jika age tidak diberikan, pakai age=25. Tentukan faktor aktivitas (AF) dari {aktv}: 0→1.2; 1–2→1.375; 3–4→1.55; 5–6→1.725; 7→1.9.
                    Kalori Maintenance = round(BMR × AF).
                    Kalori Surplus (Bulking) = round(Maintenance × 1.15).
                    Kalori Defisit (Cutting) = round(Maintenance × 0.85).
                    Output HANYA 3 baris persis seperti format ini tanpa teks lain:
                    Kalori Maintenance       : ...kcal
                    Kalori Surplus (Bulking) : ...kcal
                    Kalori Defisit (Cutting) : ...kcal"""

        if not errors:
            suksess = panggilAi(prompt)
            flash(suksess)
            return redirect(url_for('cekKalori'))
        else:
            return render_template("cekKalori.html", errors = errors, inputUser = inputUser)
    
    pesan = get_flashed_messages()
    suksess = pesan[0] if pesan else None;
    return render_template("cekKalori.html", suksess = suksess, errors = errors, inputUser = {})

@app.route("/programLatihan", methods=['GET', 'POST'])
def programLatihan():
    errors = {}
    inputUser = {}
    suksess = None

    if(request.method == 'POST'):
        maxHariLatihan = request.form.get('maxHariLatihan', '').strip()
        lamaLatihan = request.form.get('lamaLatihan', '').strip()
        action = request.form.get('action', 'create')
        suksess_text = request.form.get('suksess_text')

        inputUser = {
            'maxHariLatihan' : maxHariLatihan,
            'lamaLatihan' : lamaLatihan
        }

        if action == 'download' and suksess_text and suksess_text.strip():
            hasil_teks = suksess_text
            program_lines = hasil_teks.splitlines()
            df_program = pd.DataFrame({'Program': program_lines})
            meta = {
                'Field': ['maxHariLatihan', 'lamaLatihan', 'generated_at'],
                'Value': [maxHariLatihan or "", lamaLatihan or "", datetime.utcnow().isoformat() + 'Z']
            }
            df_meta = pd.DataFrame(meta)

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_program.to_excel(writer, sheet_name='Program', index=False)
                df_meta.to_excel(writer, sheet_name='Meta', index=False)
            output.seek(0)

            filename = f"program_latihan_{maxHariLatihan or 'X'}hari_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.xlsx"
            return send_file(
                output,
                as_attachment=True,
                download_name=filename,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )


        if not maxHariLatihan:
            errors['maxHariLatihan'] = "Inputan tidak boleh kosong!"
        else:
            try:
                inputMaxLat = int(maxHariLatihan)
                if not (1 <= inputMaxLat <= 7):
                    errors['maxHariLatihan'] = "Inputan tidak boleh kurang dari 1 dan lebih dari 7!"
            except ValueError:
                errors['maxHariLatihan'] = "Inputan hanya dapat di isi dengan angka!"

        if not lamaLatihan:
            errors['lamaLatihan'] = "Inputan tidak boleh kosong!"
        else:
            try:
                inputLamaLat = float(lamaLatihan)
                if inputLamaLat <= 0:
                    errors['lamaLatihan'] = "Inputan lama latihan minimal diatas 0!"
            except ValueError:
                errors['lamaLatihan'] = "Inputan hanya dapat di isi dengan angka!"

        prompt = f"""Tolong buatkan program latihan gym mingguan yang optimal untuk hipertrofi berdasarkan hari luang dan lama pengalaman gym pengguna. Gunakan format output **persis** seperti contoh di bawah (hari: nama split -> tiap otot -> daftar latihan dengan set & rep). Jangan ubah struktur atau format contoh; hanya sesuaikan isi sesuai input.
                    Input:
                    - hari latihan per minggu = {maxHariLatihan}  # integer
                    - pengalaman gym = {lamaLatihan} tahun  # angka desimal atau integer

                    Aturan utama pembuatan program:
                    1. Jika {maxHariLatihan} > 3 → rancang split yang membuat setiap kelompok otot **minimal dilatih 2x/minggu** (kombinasikan split push/pull/legs, upper/lower, atau PPL agar volume/jadwal terpenuhi).
                    2. Jika {maxHariLatihan} <= 2 → rancang program **full-body** yang melatih semua kelompok otot dalam tiap sesi.
                    3. Jika pengalaman {lamaLatihan} > 0 → berikan **opsi science-based lifter / heavy-duty (high intensity, low volume)**: fokus mechanical tension, target beban **80–90% 1RM**, **2–3 set per latihan** untuk mayoritas latihan utama, tetap penuhi total mingguan yang wajar untuk otot besar.
                    4. Jika pengalaman {lamaLatihan} == 0 (kurang dari 1 tahun) → berikan program **volume-moderate tinggi** fokus mind–muscle connection: lebih banyak set/reps (contoh 3–5 set pada banyak latihan), repetisi dalam rentang hipertrofi (6–20), tempo terkontrol, dan variasi isolasi.
                    5. Target volume panduan untuk pembuatan program (hanya sebagai aturan desain, jangan tampilkan kecuali diminta): otot besar ≈ **10–20 set/minggu**, otot kecil ≈ **6–12 set/minggu**. Sesuaikan pembagian set per sesi agar tercapai.
                    6. Untuk setiap hari, pilih kombinasi **compound + isolation** sesuai contoh; letakkan latihan compound di awal sesi.
                    7. Sertakan set, rentang repetisi, dan (jika relevan) rekomendasi intensitas (mis. %1RM atau RPE) dalam format contoh.
                    8. Istirahat antar set tidak perlu dicantumkan kecuali penting; fokus pada latihan, set, dan rep sesuai format.
                    9. Program harus menerapkan prinsip **progressive overload** dan keseimbangan antar otot (push vs pull).
                    10. Hindari penjelasan panjang: **Output utama hanya program** sesuai format yang kamu berikan. Setelah program, tambahkan **satu paragraf singkat** (2–3 kalimat) menjelaskan apakah set sebaiknya dilakukan *mendekati failure* atau sampai failure untuk hipertrofi, serta rekomendasi singkat tentang kapan menyarankan mendekati failure (mis. set terakhir, teknik drop, dll.).

                    Contoh format keluaran yang harus dipertahankan (contoh hanya ilustrasi, jangan ulangi selain format):
                    Senin (Push day) : Chest, Shoulder (Front / Lateral), Triceps
                    -> Chest    :   1.) Incline Press (Machine / Dumble) (2-3 set, 6-8 reps)
                                    2.) Cable Cross Over (2-3 set, 8-12reps)
                                    3.) Chest Press (2-3 set, 7-10reps)
                    ... (dst sesuai contoh lengkap yang saya berikan)

                    Catatan tambahan untuk pembuat program (internal, jangan tampilkan kecuali diminta):
                    - Berpedoman pada evidence-based hypertrophy coaching (frekuensi 2x/minggu per otot bila memungkinkan, progressive overload, variasi beban & rep, kontrol tempo).
                    - Jika perlu buat varian latihan bila alat gym terbatas, sertakan alternatif singkat dalam tanda kurung seperti pada contoh.

                    Permintaan output:
                    - Hasilkan program lengkap sesuai jumlah hari {maxHariLatihan} dan pengalaman {lamaLatihan} tahun.
                    - Jangan berikan penjelasan panjang tetapi langsung keluarkan program latihan saja."""
        
        suksess = panggilAi(prompt)
        
        if errors:
            return render_template("programLatihan.html", errors = errors, inputUser = inputUser)
        
        if action == 'create':
            flash(suksess)
            return redirect(url_for('programLatihan'))
        
        hasilTeks = suksess
        program_lines = hasilTeks.splitlines()
        
        #Data frame sederhana : setiap baris sebgai row
        df_program = pd.DataFrame({'Program': program_lines})

        #Meta data (info output)
        meta = {
            'Field': ['maxHariLatihan', 'lamaLatihan', 'generated_at'],
            'Value': [maxHariLatihan, lamaLatihan, datetime.utcnow().isoformat() + 'Z']
        }
        df_meta = pd.DataFrame(meta)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_program.to_excel(writer, sheet_name='Program', index=False)
            df_meta.to_excel(writer, sheet_name='Meta', index=False)
            writer.save()
        output.seek(0)

        filename = f"program_latihan_{maxHariLatihan}hari_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.xlsx"

        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        
    pesan = get_flashed_messages()
    suksess = pesan[0] if pesan else None;
    return render_template("programLatihan.html", suksess = suksess, errors = errors, inputUser = inputUser or {})

if __name__ == "__main__":
    app.run(debug=False)
