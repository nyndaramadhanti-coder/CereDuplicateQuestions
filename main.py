import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import csv
import io

# ─── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard Soal Duplikat",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"], p, div, span, li { font-family: 'Plus Jakarta Sans', sans-serif !important; }
.main { background: #080b18; }
.block-container { padding: 1.5rem 2rem 3rem; max-width: 1500px; }

.top-header {
  background: linear-gradient(135deg, #0f1535 0%, #080b18 60%);
  border: 1px solid #1a2050;
  border-radius: 18px;
  padding: 2rem 2.5rem;
  margin-bottom: 1.5rem;
  position: relative;
  overflow: hidden;
}
.top-header::after {
  content:'';
  position:absolute; top:-80px; right:-80px;
  width:320px; height:320px;
  background: radial-gradient(circle, rgba(99,102,241,0.12) 0%, transparent 70%);
}
.top-header h1 { font-family:'IBM Plex Mono',monospace !important; font-size:1.9rem; color:#e8ebff; margin:0 0 .3rem; letter-spacing:-1px; }
.top-header p  { color:#5a6899; font-size:.9rem; margin:0; }
.pill { display:inline-block; background:rgba(99,102,241,.18); color:#818cf8; border:1px solid rgba(99,102,241,.35); border-radius:999px; font-size:.72rem; font-family:'IBM Plex Mono',monospace !important; padding:2px 12px; letter-spacing:1px; margin-bottom:.7rem; }

.kpi-wrap { background:#0c1028; border:1px solid #161d40; border-radius:14px; padding:1.3rem 1.5rem; position:relative; overflow:hidden; height:100%; }
.kpi-wrap .accent { position:absolute; top:0;left:0; width:100%; height:3px; border-radius:14px 14px 0 0; }
.kpi-wrap .lbl { font-size:.71rem; color:#505e8a; text-transform:uppercase; letter-spacing:1.8px; font-family:'IBM Plex Mono',monospace !important; margin-bottom:.45rem; }
.kpi-wrap .val { font-size:2rem; font-family:'IBM Plex Mono',monospace !important; font-weight:600; color:#dde4ff; line-height:1; }
.kpi-wrap .sub { font-size:.76rem; color:#3a4568; margin-top:.35rem; }

.sec { font-family:'IBM Plex Mono',monospace !important; font-size:.78rem; color:#6366f1; text-transform:uppercase; letter-spacing:2px; margin-bottom:.8rem; padding-bottom:.5rem; border-bottom:1px solid #161d40; }

.action-critical { background:#2d0f1a; border:1px solid #7f1d35; border-radius:10px; padding:.8rem 1.1rem; margin-bottom:.6rem; }
.action-critical .title { color:#f87171; font-weight:600; font-size:.85rem; margin-bottom:.3rem; }
.action-critical .desc  { color:#9a6472; font-size:.8rem; line-height:1.5; }
.action-warn { background:#1e1a06; border:1px solid #6b5000; border-radius:10px; padding:.8rem 1.1rem; margin-bottom:.6rem; }
.action-warn .title { color:#fbbf24; font-weight:600; font-size:.85rem; margin-bottom:.3rem; }
.action-warn .desc  { color:#8a7a40; font-size:.8rem; line-height:1.5; }
.action-info { background:#071822; border:1px solid #0e4a6e; border-radius:10px; padding:.8rem 1.1rem; margin-bottom:.6rem; }
.action-info .title { color:#38bdf8; font-weight:600; font-size:.85rem; margin-bottom:.3rem; }
.action-info .desc  { color:#3a7090; font-size:.8rem; line-height:1.5; }

.bank-card { background:#0c1028; border:1px solid #1a2250; border-radius:14px; padding:1.3rem 1.5rem; margin-bottom:1rem; }
.bank-card .bank-id { font-family:'IBM Plex Mono',monospace !important; font-size:1.2rem; color:#818cf8; font-weight:600; }
.bank-card .tag { background:#161d40; color:#7b86b8; border-radius:6px; padding:2px 10px; font-size:.75rem; display:inline-block; margin:2px; }

[data-testid="stSidebar"] { background:#080b18; border-right:1px solid #161d40; }
</style>
""", unsafe_allow_html=True)


# ─── Load & Process Data ───────────────────────────────────────────────────────
@st.cache_data
def load_data(path):
    rows = []
    with open(path, newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            if row:
                inner = row[0]
                for ir in csv.reader([inner]):
                    rows.append(ir)
    df = pd.DataFrame(rows[1:], columns=rows[0])
    df['question_id']      = pd.to_numeric(df['question_id'], errors='coerce')
    df['bank_question_id'] = pd.to_numeric(df['bank_question_id'], errors='coerce')
    df['question_number']  = pd.to_numeric(df['question_number'], errors='coerce')

    bank = df.groupby('bank_question_id').agg(
        dup_count     = ('question_id', 'size'),
        platforms     = ('Platform', lambda x: sorted(x.unique())),
        n_platforms   = ('Platform', 'nunique'),
        categories    = ('category_name', lambda x: sorted(x.unique())),
        n_categories  = ('category_name', 'nunique'),
        content_types = ('content_type', lambda x: sorted(x.unique())),
        question_ids  = ('question_id', lambda x: sorted(x.tolist())),
    ).reset_index()

    bank['platforms_str']     = bank['platforms'].apply(lambda x: ', '.join(x))
    bank['categories_str']    = bank['categories'].apply(lambda x: ', '.join(x))
    bank['content_types_str'] = bank['content_types'].apply(lambda x: ', '.join(x))

    def severity(row):
        if row['n_platforms'] >= 3: return 'KRITIS'
        if row['n_platforms'] == 2 and row['dup_count'] >= 5: return 'TINGGI'
        if row['n_platforms'] == 2: return 'SEDANG'
        if row['dup_count'] >= 5: return 'PERHATIAN'
        return 'RENDAH'
    bank['severity'] = bank.apply(severity, axis=1)

    df2 = df.merge(bank[['bank_question_id','dup_count','n_platforms','platforms_str','severity']], on='bank_question_id')
    return df2, bank

df, bank = load_data('soalduplikat.csv')

SEV_COLOR = {'KRITIS':'#ef4444','TINGGI':'#f97316','SEDANG':'#fbbf24','PERHATIAN':'#38bdf8','RENDAH':'#34d399'}
PLOT_THEME = dict(paper_bgcolor='#0c1028', plot_bgcolor='#0c1028',
                  font=dict(family='Plus Jakarta Sans', color='#8891b8'))

# ─── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔧 Filter Global")
    st.markdown("---")
    sel_plat  = st.selectbox("Platform",  ["Semua"] + sorted(df['Platform'].unique()))
    sel_type  = st.selectbox("Tipe Konten", ["Semua"] + sorted(df['content_type'].unique()))
    sel_sev   = st.selectbox("Severity", ["Semua","KRITIS","TINGGI","SEDANG","PERHATIAN","RENDAH"])
    sel_nplat = st.selectbox("Jenis Duplikat", ["Semua","1 platform","2 platform","3 platform"])
    top_n     = st.slider("Top N untuk charts", 5, 30, 15)
    st.markdown("---")
    st.markdown(f"<div style='font-family:IBM Plex Mono,monospace;font-size:.72rem;color:#2a3060;'>Total baris: {len(df):,}<br>Bank soal unik: {bank['bank_question_id'].nunique():,}</div>", unsafe_allow_html=True)

# Apply filters
fdf   = df.copy()
fbank = bank.copy()
if sel_plat  != "Semua": fdf = fdf[fdf['Platform']==sel_plat]; fbank = fbank[fbank['platforms_str'].str.contains(sel_plat)]
if sel_type  != "Semua": fdf = fdf[fdf['content_type']==sel_type]
if sel_sev   != "Semua": fdf = fdf[fdf['severity']==sel_sev];  fbank = fbank[fbank['severity']==sel_sev]
if sel_nplat != "Semua":
    n = int(sel_nplat[0]); fdf = fdf[fdf['n_platforms']==n]; fbank = fbank[fbank['n_platforms']==n]

# ─── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="top-header">
  <div class="pill">QUALITY CONTROL · BANK SOAL</div>
  <h1>🔍 Dashboard Soal Duplikat</h1>
  <p>Analisis mendalam duplikasi soal lintas platform · Cerebrum · JadiBUMN · JadiASN</p>
</div>""", unsafe_allow_html=True)

# ─── KPI ───────────────────────────────────────────────────────────────────────
k = st.columns(6)
def kpi(col, lbl, val, sub, color):
    col.markdown(f"""<div class="kpi-wrap"><div class="accent" style="background:{color}"></div>
    <div class="lbl">{lbl}</div><div class="val">{val}</div><div class="sub">{sub}</div></div>""", unsafe_allow_html=True)

kpi(k[0], "Bank Soal Duplikat",  f"{fbank['bank_question_id'].nunique():,}", "grup unik", "#6366f1")
kpi(k[1], "Total Kemunculan",    f"{len(fdf):,}",                           "baris data", "#8b5cf6")
kpi(k[2], "Lintas Platform",     f"{(fbank['n_platforms']>1).sum():,}",     "2–3 platform", "#ec4899")
kpi(k[3], "Duplikat KRITIS",     f"{(fbank['severity']=='KRITIS').sum():,}","3 platform sekaligus", "#ef4444")
kpi(k[4], "Maks Duplikasi",      f"{int(fbank['dup_count'].max()) if len(fbank)>0 else 0}x", "1 bank soal", "#f59e0b")
kpi(k[5], "Avg Duplikasi",       f"{round(fbank['dup_count'].mean(),1) if len(fbank)>0 else 0}x", "per bank soal", "#10b981")
st.markdown("<br>", unsafe_allow_html=True)

# ─── TABS ──────────────────────────────────────────────────────────────────────
tabs = st.tabs(["📊 Ringkasan","🏦 Analisis Bank Soal","🌐 Cross-Platform","📂 Kategori & Konten","⚠️ Prioritas Tindakan","🔎 Detail & Ekspor"])

# ══════════════ TAB 1: RINGKASAN ══════════════
with tabs[0]:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="sec">Distribusi Tingkat Keparahan</div>', unsafe_allow_html=True)
        sev_c = fbank['severity'].value_counts().reindex(['KRITIS','TINGGI','SEDANG','PERHATIAN','RENDAH']).fillna(0).reset_index()
        sev_c.columns = ['Severity','Count']
        fig = go.Figure(go.Bar(x=sev_c['Severity'], y=sev_c['Count'],
            marker_color=[SEV_COLOR.get(s,'#6366f1') for s in sev_c['Severity']],
            text=sev_c['Count'], texttemplate='%{text:,}', textposition='outside', marker_line_width=0))
        fig.update_layout(**PLOT_THEME, margin=dict(t=20,b=20,l=10,r=10), height=280,
            xaxis=dict(showgrid=False,color='#3a4568'), yaxis=dict(showgrid=True,gridcolor='#161d40',color='#3a4568'))
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown('<div class="sec">Platform vs Tipe Konten</div>', unsafe_allow_html=True)
        cross = fdf.groupby(['Platform','content_type']).size().reset_index(name='count')
        fig2 = px.bar(cross, x='Platform', y='count', color='content_type', barmode='stack',
            color_discrete_map={'Tryout':'#6366f1','Latsol':'#ec4899'}, text='count')
        fig2.update_traces(texttemplate='%{text:,}', textposition='inside', marker_line_width=0)
        fig2.update_layout(**PLOT_THEME, margin=dict(t=20,b=20,l=10,r=10), height=280,
            legend=dict(bgcolor='rgba(0,0,0,0)'),
            xaxis=dict(showgrid=False,color='#3a4568'), yaxis=dict(showgrid=True,gridcolor='#161d40',color='#3a4568'))
        st.plotly_chart(fig2, use_container_width=True)

    c3, c4 = st.columns([2,1])
    with c3:
        st.markdown('<div class="sec">Histogram Duplikasi Per Bank Soal</div>', unsafe_allow_html=True)
        hist = fbank['dup_count'].value_counts().sort_index().reset_index()
        hist.columns = ['Jumlah Duplikat','Frekuensi']
        fig3 = px.bar(hist, x='Jumlah Duplikat', y='Frekuensi', color='Frekuensi',
            color_continuous_scale=['#1a2050','#6366f1','#ec4899'], text='Frekuensi')
        fig3.update_traces(texttemplate='%{text:,}', textposition='outside', marker_line_width=0)
        fig3.update_layout(**PLOT_THEME, coloraxis_showscale=False, margin=dict(t=20,b=20,l=10,r=10), height=280,
            xaxis=dict(showgrid=False,color='#3a4568',title='Jumlah Kemunculan'),
            yaxis=dict(showgrid=True,gridcolor='#161d40',color='#3a4568',title='Jml Bank Soal'))
        st.plotly_chart(fig3, use_container_width=True)

    with c4:
        st.markdown('<div class="sec">Ringkasan Cepat</div>', unsafe_allow_html=True)
        items = [
            ("Duplikat 2x",      f"{(fbank['dup_count']==2).sum():,} bank soal",                  "#34d399"),
            ("Duplikat 3–5x",    f"{((fbank['dup_count']>=3)&(fbank['dup_count']<=5)).sum():,} bank soal", "#fbbf24"),
            ("Duplikat 6x+",     f"{(fbank['dup_count']>=6).sum():,} bank soal",                  "#ef4444"),
            ("1 platform saja",  f"{(fbank['n_platforms']==1).sum():,} bank soal",                "#38bdf8"),
            ("2 platform",       f"{(fbank['n_platforms']==2).sum():,} bank soal",                "#a78bfa"),
            ("3 platform",       f"{(fbank['n_platforms']==3).sum():,} bank soal",                "#ef4444"),
        ]
        for lbl, val, c in items:
            st.markdown(f"""<div style='display:flex;justify-content:space-between;align-items:center;
              padding:.55rem .8rem;margin-bottom:.4rem;background:#0c1028;border:1px solid #161d40;
              border-radius:8px;border-left:3px solid {c};'>
              <span style='color:#8891b8;font-size:.82rem;'>{lbl}</span>
              <span style='color:{c};font-family:IBM Plex Mono,monospace;font-weight:600;font-size:.85rem;'>{val}</span>
            </div>""", unsafe_allow_html=True)


# ══════════════ TAB 2: ANALISIS BANK SOAL ══════════════
with tabs[1]:
    st.markdown('<div class="sec">Top Bank Soal Dengan Duplikat Terbanyak</div>', unsafe_allow_html=True)
    top_bank = fbank.sort_values('dup_count', ascending=False).head(top_n).copy()
    top_bank['bid_str'] = top_bank['bank_question_id'].astype(str)
    fig_tb = px.bar(top_bank.sort_values('dup_count'), x='dup_count', y='bid_str',
        orientation='h', color='severity', color_discrete_map=SEV_COLOR, text='dup_count',
        hover_data={'platforms_str':True,'n_categories':True,'n_platforms':True,'bid_str':False})
    fig_tb.update_traces(texttemplate='%{text}x', textposition='outside', marker_line_width=0)
    fig_tb.update_layout(**PLOT_THEME, margin=dict(t=20,b=20,l=80,r=60), height=max(350,top_n*30),
        legend=dict(bgcolor='rgba(0,0,0,0)', title='Severity'),
        xaxis=dict(showgrid=True,gridcolor='#161d40',color='#3a4568',title='Jumlah Kemunculan'),
        yaxis=dict(showgrid=False,color='#9aa5c4',title='Bank Question ID',
                   tickfont=dict(family='IBM Plex Mono',size=10)))
    st.plotly_chart(fig_tb, use_container_width=True)

    # Detail cards
    st.markdown('<div class="sec">Kartu Detail — Top 10 Bank Soal Terduplikat</div>', unsafe_allow_html=True)
    for _, row in fbank.sort_values('dup_count', ascending=False).head(10).iterrows():
        sc = SEV_COLOR.get(row['severity'],'#6366f1')
        cats  = row['categories'][:5]
        extra_c = len(row['categories']) - 5
        q_ids = row['question_ids'][:8]
        extra_q = len(row['question_ids']) - 8

        plat_tags = ''.join([f"<span class='tag'>{p}</span>" for p in row['platforms']])
        sev_tag   = f"<span class='tag' style='background:{sc}20;color:{sc};border:1px solid {sc}40;'>{row['severity']}</span>"
        cat_tags  = ''.join([f"<span class='tag'>{c[:45]}{'…' if len(c)>45 else ''}</span>" for c in cats])
        if extra_c > 0: cat_tags += f"<span class='tag'>+{extra_c} lainnya</span>"
        qid_tags  = ''.join([f"<span class='tag'>{int(q)}</span>" for q in q_ids])
        if extra_q > 0: qid_tags += f"<span class='tag'>+{extra_q} lagi</span>"

        st.markdown(f"""
        <div class="bank-card" style="border-left:4px solid {sc};">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;">
            <div class="bank-id">Bank ID: {int(row['bank_question_id'])}</div>
            <div style="display:flex;gap:.5rem;align-items:center;">
              {sev_tag}
              <span style="font-family:IBM Plex Mono,monospace;font-size:1.3rem;color:{sc};font-weight:700;">{int(row['dup_count'])}x</span>
            </div>
          </div>
          <div style="margin-top:.6rem;">
            <div style="color:#3a4568;font-size:.7rem;text-transform:uppercase;letter-spacing:1px;margin-bottom:.3rem;">Platform ({int(row['n_platforms'])})</div>
            <div>{plat_tags}</div>
          </div>
          <div style="margin-top:.7rem;">
            <div style="color:#3a4568;font-size:.7rem;text-transform:uppercase;letter-spacing:1px;margin-bottom:.3rem;">Kategori ({int(row['n_categories'])})</div>
            <div>{cat_tags}</div>
          </div>
          <div style="margin-top:.7rem;">
            <div style="color:#3a4568;font-size:.7rem;text-transform:uppercase;letter-spacing:1px;margin-bottom:.3rem;">Question IDs ({len(row['question_ids'])} soal)</div>
            <div>{qid_tags}</div>
          </div>
        </div>""", unsafe_allow_html=True)

    # Scatter
    st.markdown('<div class="sec">Scatter: Jumlah Duplikat vs Jumlah Kategori (per bank soal)</div>', unsafe_allow_html=True)
    sc_df = fbank.copy(); sc_df['bid_str'] = sc_df['bank_question_id'].astype(str)
    fig_sc = px.scatter(sc_df, x='dup_count', y='n_categories', color='severity',
        color_discrete_map=SEV_COLOR, size='dup_count', size_max=25,
        hover_name='bid_str', opacity=0.75,
        labels={'dup_count':'Jumlah Duplikat','n_categories':'Jumlah Kategori Berbeda'})
    fig_sc.update_layout(**PLOT_THEME, margin=dict(t=20,b=20,l=10,r=10), height=350,
        legend=dict(bgcolor='rgba(0,0,0,0)'),
        xaxis=dict(showgrid=True,gridcolor='#161d40',color='#3a4568'),
        yaxis=dict(showgrid=True,gridcolor='#161d40',color='#3a4568'))
    st.plotly_chart(fig_sc, use_container_width=True)


# ══════════════ TAB 3: CROSS-PLATFORM ══════════════
with tabs[2]:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="sec">Heatmap Tumpang Tindih Antar Platform</div>', unsafe_allow_html=True)
        platforms = sorted(df['Platform'].unique())
        heat = []
        for p1 in platforms:
            ids1 = set(df[df['Platform']==p1]['bank_question_id'])
            heat.append([len(ids1 & set(df[df['Platform']==p2]['bank_question_id'])) for p2 in platforms])
        fig_h = go.Figure(go.Heatmap(z=heat, x=platforms, y=platforms,
            colorscale=[[0,'#0c1028'],[0.5,'#312e81'],[1,'#6366f1']],
            text=heat, texttemplate='%{text:,}',
            textfont=dict(size=18,color='white',family='IBM Plex Mono'), showscale=True))
        fig_h.update_layout(**PLOT_THEME, margin=dict(t=20,b=20,l=10,r=10), height=320,
            xaxis=dict(color='#9aa5c4'), yaxis=dict(color='#9aa5c4'))
        st.plotly_chart(fig_h, use_container_width=True)

    with c2:
        st.markdown('<div class="sec">Distribusi Kombinasi Platform</div>', unsafe_allow_html=True)
        combo = fbank['platforms_str'].value_counts().reset_index()
        combo.columns = ['Kombinasi','Jumlah']
        fig_combo = px.pie(combo, names='Kombinasi', values='Jumlah', hole=0.55,
            color_discrete_sequence=['#6366f1','#ec4899','#f59e0b','#10b981','#38bdf8'])
        fig_combo.update_traces(textinfo='label+percent', marker=dict(line=dict(color='#080b18',width=3)))
        fig_combo.update_layout(**PLOT_THEME, margin=dict(t=20,b=20,l=10,r=10), height=320,
            legend=dict(bgcolor='rgba(0,0,0,0)'))
        st.plotly_chart(fig_combo, use_container_width=True)

    st.markdown('<div class="sec">Bank Soal Muncul di Semua 3 Platform (Paling Kritis)</div>', unsafe_allow_html=True)
    all3 = fbank[fbank['n_platforms']==3].sort_values('dup_count', ascending=False).head(50)
    if len(all3) > 0:
        d = all3[['bank_question_id','dup_count','n_categories','categories_str','content_types_str']].copy()
        d.columns = ['Bank ID','Jml Duplikat','Jml Kategori','Kategori','Tipe Konten']
        st.dataframe(d.reset_index(drop=True), use_container_width=True, height=300)
    else:
        st.info("Tidak ada data dengan filter ini.")

    st.markdown('<div class="sec">Soal Eksklusif vs Dibagikan Per Platform</div>', unsafe_allow_html=True)
    excl_data = []
    for p in platforms:
        p_ids = set(df[df['Platform']==p]['bank_question_id'])
        others = set(df[df['Platform']!=p]['bank_question_id'])
        excl_data.append({'Platform':p, 'Eksklusif':len(p_ids - others), 'Dibagikan':len(p_ids & others)})
    fig_excl = px.bar(pd.DataFrame(excl_data), x='Platform', y=['Eksklusif','Dibagikan'],
        color_discrete_map={'Eksklusif':'#6366f1','Dibagikan':'#ec4899'}, barmode='group', text_auto=True)
    fig_excl.update_layout(**PLOT_THEME, margin=dict(t=20,b=20,l=10,r=10), height=300,
        legend=dict(bgcolor='rgba(0,0,0,0)'),
        xaxis=dict(showgrid=False,color='#3a4568'), yaxis=dict(showgrid=True,gridcolor='#161d40',color='#3a4568'))
    st.plotly_chart(fig_excl, use_container_width=True)


# ══════════════ TAB 4: KATEGORI & KONTEN ══════════════
with tabs[3]:
    c1, c2 = st.columns([3,2])
    with c1:
        st.markdown(f'<div class="sec">Top {top_n} Kategori — Total Kemunculan</div>', unsafe_allow_html=True)
        cat_c = fdf.groupby('category_name').size().nlargest(top_n).reset_index()
        cat_c.columns = ['Kategori','Jumlah']
        cat_c['KatShort'] = cat_c['Kategori'].str[:50]+'…'
        fig_cat = px.bar(cat_c.sort_values('Jumlah'), x='Jumlah', y='KatShort', orientation='h',
            color='Jumlah', color_continuous_scale=['#1a2050','#6366f1','#ec4899'], text='Jumlah')
        fig_cat.update_traces(texttemplate='%{text:,}', textposition='outside', marker_line_width=0)
        fig_cat.update_layout(**PLOT_THEME, coloraxis_showscale=False, margin=dict(t=20,b=20,l=10,r=60),
            height=max(350,top_n*28), xaxis=dict(showgrid=True,gridcolor='#161d40',color='#3a4568'),
            yaxis=dict(showgrid=False,color='#9aa5c4',title=''))
        st.plotly_chart(fig_cat, use_container_width=True)

    with c2:
        st.markdown(f'<div class="sec">Top {top_n} Kategori — Avg Duplikat</div>', unsafe_allow_html=True)
        cat_avg = fdf.groupby('category_name').agg(total=('question_id','size'), ubk=('bank_question_id','nunique')).reset_index()
        cat_avg['avg'] = (cat_avg['total']/cat_avg['ubk']).round(2)
        cat_avg = cat_avg[cat_avg['ubk']>=5].nlargest(top_n,'avg')
        cat_avg['KatShort'] = cat_avg['category_name'].str[:45]+'…'
        fig_avg = px.bar(cat_avg.sort_values('avg'), x='avg', y='KatShort', orientation='h',
            color='avg', color_continuous_scale=['#1a2050','#f59e0b','#ef4444'], text='avg')
        fig_avg.update_traces(texttemplate='%{text:.2f}x', textposition='outside', marker_line_width=0)
        fig_avg.update_layout(**PLOT_THEME, coloraxis_showscale=False, margin=dict(t=20,b=20,l=10,r=60),
            height=max(350,top_n*28), xaxis=dict(showgrid=True,gridcolor='#161d40',color='#3a4568'),
            yaxis=dict(showgrid=False,color='#9aa5c4',title=''))
        st.plotly_chart(fig_avg, use_container_width=True)

    st.markdown('<div class="sec">Statistik Lengkap Per Kategori</div>', unsafe_allow_html=True)
    cat_stats = fdf.groupby('category_name').agg(
        total_rows  = ('question_id','size'),
        unique_bank = ('bank_question_id','nunique'),
        platforms   = ('Platform', lambda x: ', '.join(sorted(x.unique()))),
        n_plat      = ('Platform','nunique'),
        content_type= ('content_type', lambda x: ', '.join(sorted(x.unique()))),
    ).reset_index()
    cat_stats['avg_dup'] = (cat_stats['total_rows']/cat_stats['unique_bank']).round(2)
    cat_stats = cat_stats.sort_values('total_rows', ascending=False).reset_index(drop=True)
    cat_stats.columns = ['Kategori','Total Baris','Bank Soal Unik','Platform','Jml Platform','Tipe','Avg Duplikat']
    srch = st.text_input("🔍 Cari kategori...", key="cat_s")
    if srch: cat_stats = cat_stats[cat_stats['Kategori'].str.contains(srch,case=False,na=False)]
    st.dataframe(cat_stats, use_container_width=True, height=380)


# ══════════════ TAB 5: PRIORITAS TINDAKAN ══════════════
with tabs[4]:
    st.markdown('<div class="sec">Rekomendasi Tindakan Berdasarkan Data</div>', unsafe_allow_html=True)

    n_kritis = (fbank['severity']=='KRITIS').sum()
    n_cross  = (fbank['n_platforms']>1).sum()
    top1     = fbank.sort_values('dup_count',ascending=False).iloc[0] if len(fbank)>0 else None

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"""
        <div class="action-critical">
          <div class="title">🚨 SEGERA — Soal Muncul di 3 Platform Sekaligus</div>
          <div class="desc">Terdapat <b style='color:#f87171'>{n_kritis:,} bank soal</b> yang muncul di Cerebrum, JadiBUMN, dan JadiASN secara bersamaan. Ini risiko tertinggi — pengguna lintas platform mengerjakan soal identik.<br><br>
          <b>Tindakan:</b> Audit setiap bank soal KRITIS. Tentukan platform "asli" pemilik soal, hapus dari platform lain, atau ganti dengan soal baru.</div>
        </div>
        <div class="action-critical">
          <div class="title">🔴 TINGGI — Bank Soal Paling Banyak Digunakan</div>
          <div class="desc">Bank ID <b style='color:#f87171'>{int(top1['bank_question_id']) if top1 is not None else '-'}</b> muncul <b style='color:#f87171'>{int(top1['dup_count']) if top1 is not None else 0}x</b> di <b>{int(top1['n_platforms']) if top1 is not None else 0} platform</b> dan <b>{int(top1['n_categories']) if top1 is not None else 0} kategori</b> yang berbeda.<br><br>
          <b>Tindakan:</b> Investigasi apakah soal ini sengaja dipakai ulang (soal fundamental) atau perlu diganti. Tetapkan batas maksimum pemakaian soal.</div>
        </div>
        """, unsafe_allow_html=True)

    with col_b:
        st.markdown(f"""
        <div class="action-warn">
          <div class="title">⚠️ SEDANG — {n_cross:,} Bank Soal Lintas Platform</div>
          <div class="desc">Ribuan soal muncul di lebih dari satu platform, memengaruhi integritas dan pengalaman pengguna multi-platform.<br><br>
          <b>Tindakan:</b> Implementasi validasi otomatis — saat upload soal, cek apakah <code>bank_question_id</code> sudah ada di platform lain. Beri alert atau blokir duplikat lintas platform.</div>
        </div>
        <div class="action-warn">
          <div class="title">⚠️ SEDANG — Kategori Tryout Populer Banyak Duplikat</div>
          <div class="desc">Kategori <b style='color:#fbbf24'>Tryout Tahap 1 RBB BUMN</b> punya 8.000+ baris duplikat karena soal dipakai ulang di banyak sesi tryout berbeda.<br><br>
          <b>Tindakan:</b> Perbesar pool bank soal untuk kategori populer. Implementasi rotasi soal otomatis agar peserta tidak melihat soal yang sama di dua tryout berbeda.</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="action-info">
      <div class="title">ℹ️ JANGKA PANJANG — Kebijakan Manajemen Bank Soal</div>
      <div class="desc">
        <b>1. Validasi upload:</b> Cek <code>bank_question_id</code> sebelum soal masuk sistem — blokir jika sudah ada di platform yang sama.<br>
        <b>2. Batas pemakaian:</b> Tetapkan maksimum berapa kali satu bank soal boleh dipakai per platform (rekomendasi: max 3x).<br>
        <b>3. Pemisahan konten platform:</b> Buat aturan soal di JadiBUMN tidak boleh identik dengan soal di Cerebrum kecuali disetujui editor.<br>
        <b>4. Monitoring rutin:</b> Jalankan dashboard ini setiap minggu. Target KPI: 0 soal KRITIS, duplikat lintas platform &lt; 10%, avg duplikat &lt; 2x.
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sec" style="margin-top:1rem;">Tabel Prioritas — Bank Soal Perlu Segera Ditindak</div>', unsafe_allow_html=True)
    prio = fbank[fbank['severity'].isin(['KRITIS','TINGGI'])].sort_values(
        ['n_platforms','dup_count'], ascending=False).head(100).copy()
    if len(prio) > 0:
        pd_disp = prio[['bank_question_id','dup_count','n_platforms','severity','platforms_str','n_categories','categories_str','content_types_str']].copy()
        pd_disp.columns = ['Bank ID','Jml Duplikat','Jml Platform','Severity','Platform','Jml Kategori','Kategori','Tipe Konten']
        st.dataframe(pd_disp.reset_index(drop=True), use_container_width=True, height=400)
        buf = io.StringIO(); pd_disp.to_csv(buf, index=False)
        st.download_button("📥 Download Daftar Prioritas (CSV)", buf.getvalue(), "prioritas_soal_duplikat.csv","text/csv")
    else:
        st.info("Tidak ada data prioritas dengan filter ini.")


# ══════════════ TAB 6: DETAIL & EKSPOR ══════════════
with tabs[5]:
    st.markdown('<div class="sec">Pencarian & Filter Detail</div>', unsafe_allow_html=True)
    cs1, cs2, cs3 = st.columns(3)
    with cs1: srch2 = st.text_input("🔍 Cari kategori / konten / platform")
    with cs2: bid_in = st.text_input("🏦 Cari Bank Question ID")
    with cs3: min_dup = st.number_input("Min duplikat", min_value=2, value=2, step=1)

    det = fdf.copy()
    if srch2:
        m = (det['category_name'].str.contains(srch2,case=False,na=False)|
             det['content_name'].str.contains(srch2,case=False,na=False)|
             det['Platform'].str.contains(srch2,case=False,na=False))
        det = det[m]
    if bid_in.strip():
        try: det = det[det['bank_question_id']==int(bid_in.strip())]
        except: st.warning("Bank ID harus angka")
    det = det[det['dup_count']>=min_dup].sort_values(['dup_count','bank_question_id'],ascending=[False,True]).reset_index(drop=True)

    st.markdown(f"<div style='color:#505e8a;font-size:.8rem;margin-bottom:.5rem;'>Menampilkan <b style='color:#8891b8'>{len(det):,}</b> baris</div>", unsafe_allow_html=True)

    sc = ['Platform','question_id','bank_question_id','question_number','category_name',
          'content_name','content_type','dup_count','n_platforms','severity','Link Video Penjelasan']
    rc = {'Platform':'Platform','question_id':'Q ID','bank_question_id':'Bank ID','question_number':'No Soal',
          'category_name':'Kategori','content_name':'Nama Konten','content_type':'Tipe',
          'dup_count':'# Duplikat','n_platforms':'# Platform','severity':'Severity','Link Video Penjelasan':'Video ID'}
    st.dataframe(det[sc].rename(columns=rc), use_container_width=True, height=450)

    st.markdown("---")
    ce1, ce2 = st.columns(2)
    with ce1:
        b1 = io.StringIO(); det[sc].rename(columns=rc).to_csv(b1, index=False)
        st.download_button("📥 Download Data Terfilter (CSV)", b1.getvalue(), "soal_duplikat_filtered.csv","text/csv")
    with ce2:
        b2 = io.StringIO()
        exp = fbank[['bank_question_id','dup_count','n_platforms','severity','platforms_str','n_categories','categories_str','content_types_str']].copy()
        exp.columns = ['Bank ID','Jml Duplikat','Jml Platform','Severity','Platform','Jml Kategori','Kategori','Tipe Konten']
        exp.sort_values('Jml Duplikat',ascending=False).to_csv(b2, index=False)
        st.download_button("📥 Download Ringkasan Bank Soal (CSV)", b2.getvalue(), "ringkasan_bank_soal.csv","text/csv")

    st.markdown('<div class="sec" style="margin-top:1.5rem;">Top Video ID Paling Sering Terduplikat</div>', unsafe_allow_html=True)
    vid = fdf.groupby('Link Video Penjelasan').size().nlargest(top_n).reset_index()
    vid.columns = ['Video ID','Jml Kemunculan']
    vid_p = fdf.groupby('Link Video Penjelasan')['Platform'].apply(lambda x:','.join(sorted(x.unique()))).reset_index()
    vid_p.columns = ['Video ID','Platform']
    vid_c = fdf.groupby('Link Video Penjelasan')['category_name'].apply(lambda x:len(x.unique())).reset_index()
    vid_c.columns = ['Video ID','Jml Kategori']
    vid = vid.merge(vid_p,on='Video ID').merge(vid_c,on='Video ID')
    st.dataframe(vid.reset_index(drop=True), use_container_width=True, height=300)

# ─── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style='text-align:center;font-family:IBM Plex Mono,monospace;font-size:.7rem;color:#1a2050;
  margin-top:2rem;padding:1rem;border-top:1px solid #161d40;'>
  Dashboard Soal Duplikat · Cerebrum · JadiBUMN · JadiASN · Streamlit + Plotly
</div>""", unsafe_allow_html=True)