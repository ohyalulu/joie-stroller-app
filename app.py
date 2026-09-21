import os
import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st

# 1. 頁面基本設定
st.set_page_config(
    page_title="Joie 推車規格系統",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 確保圖片目錄存在
if not os.path.exists("images"):
  os.makedirs("images")


def get_connection():
  return sqlite3.connect("strollers.db")


def load_data():
  conn = get_connection()
  df = pd.read_sql("SELECT * FROM strollers", conn)
  conn.close()
  return df


# -------------------------------------------------------------
# 側邊欄：外觀顏色與版面排序控制台 (不需寫程式碼即可改)
# -------------------------------------------------------------
st.sidebar.title("🛠️ 推車規格管理系統")

with st.sidebar.expander("🎨 網頁外觀與排序設定", expanded=False):
  # 預設主題快速切換
  theme_choice = st.selectbox(
      "品牌配色預設：", ["Joie 經典橘", "森林暖綠", "沉穩深藍", "自訂顏色"]
  )

  if theme_choice == "Joie 經典橘":
    primary_color = "#FF8200"
    tag_bg = "#FFF3E6"
  elif theme_choice == "森林暖綠":
    primary_color = "#00A389"
    tag_bg = "#E6F6F3"
  elif theme_choice == "沉穩深藍":
    primary_color = "#1D4ED8"
    tag_bg = "#EFF6FF"
  else:
    primary_color = st.color_picker("選擇主品牌色：", "#FF8200")
    tag_bg = "#FFF3E6"

  # 模組版面排序 (用拖曳或選取順序決定頁面上下位置)
  st.write("---")
  st.markdown("**📋 調整比對頁面區塊順序：**")
  section_order = st.multiselect(
      "拖曳或調整顯示順序：",
      options=["📷 產品外觀照片", "📋 詳細規格對照表", "📊 關鍵規格圖表"],
      default=["📷 產品外觀照片", "📋 詳細規格對照表", "📊 關鍵規格圖表"],
  )

# 動態注入 CSS 樣式 (由使用者選擇的顏色決定)
st.markdown(
    f"""
<style>
    .stApp {{
        background-color: #FBFBFB !important;
    }}
    /* 按鈕主色調 */
    .stButton > button, div[data-testid="stFormSubmitButton"] > button {{
        background-color: {primary_color} !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 20px !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1) !important;
    }}
    /* 標籤 Tag 配色 */
    span[data-baseweb="tag"] {{
        background-color: {tag_bg} !important;
        color: {primary_color} !important;
        border: 1px solid {primary_color} !important;
    }}
    /* 產品外觀卡片樣式 */
    .stroller-card {{
        background-color: #FFFFFF;
        border-radius: 14px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
        border: 1px solid #EFEFEF;
        margin-bottom: 12px;
    }}
</style>
""",
    unsafe_allow_html=True,
)

# 頁面切換選單
page = st.sidebar.radio(
    "功能選單", ["🔍 型號規格比對", "📋 規格總覽清單", "➕ 新增/編輯型號"]
)

df = load_data()

# -------------------------------------------------------------
# 頁面 1: 規格比對
# -------------------------------------------------------------
if page == "🔍 型號規格比對":
  st.header("⚖️ 推車型號規格並排比對")

  df["Display_Label"] = (
      df["Model_Number"]
      + " - "
      + df["Product_Name"]
      + " ("
      + df["Fashion"].fillna("")
      + ")"
  )

  selected_models = st.multiselect(
      "請選擇要比對的推車型號 (建議 2~4 台)：",
      options=df["Display_Label"].tolist(),
      default=df["Display_Label"].tolist()[:2]
      if len(df) >= 2
      else df["Display_Label"].tolist(),
  )

  if selected_models:
    compare_df = df[df["Display_Label"].isin(selected_models)].copy()

    # 封裝三個展示區塊，供下方動態排序呼叫
    def render_photos():
      st.subheader("📷 產品外觀照片")
      img_cols = st.columns(len(compare_df))
      for idx, (_, row) in enumerate(compare_df.iterrows()):
        with img_cols[idx]:
          model_num = row["Model_Number"]
          jpg_img = f"images/{model_num}.jpg"
          png_img = f"images/{model_num}.png"
          if os.path.exists(jpg_img):
            st.image(jpg_img, use_container_width=True)
          elif os.path.exists(png_img):
            st.image(png_img, use_container_width=True)
          else:
            st.markdown(
                f"""
                        <div class="stroller-card">
                            <div style="font-size: 36px; color: #94A3B8;">📷</div>
                            <p style="color: #64748B; font-size: 13px; margin-top: 6px;">尚無照片<br><code>{model_num}</code></p>
                        </div>
                        """,
                unsafe_allow_html=True,
            )
          st.caption(
              f"**{row['Product_Name']}** ({row['Fashion'] or '標準版'})"
          )

    def render_table():
      st.subheader("📋 詳細規格對照表")
      display_cols = [
          "Product_Name",
          "Model_Number",
          "Item_Code",
          "Fashion",
          "Product_Usage",
          "Product_Weight_kg",
          "Front_Wheel_Size",
          "Rear_Wheel_Size",
          "Wheel_Type",
          "Wheel_Suspension",
          "One_Hand_Fold",
          "Basket_Capacity_kg",
          "Folded_L",
          "Folded_W",
          "Folded_H",
          "Certification",
      ]
      subset = compare_df.set_index("Display_Label")[display_cols].T
      st.dataframe(subset, use_container_width=True)

    def render_charts():
      st.subheader("📊 關鍵規格圖表")
      c1, c2 = st.columns(2)
      with c1:
        try:
          compare_df["Weight_Num"] = pd.to_numeric(
              compare_df["Product_Weight_kg"], errors="coerce"
          )
          fig_w = px.bar(
              compare_df,
              x="Display_Label",
              y="Weight_Num",
              title="車身重量 (kg)",
              text="Weight_Num",
              color="Display_Label",
          )
          st.plotly_chart(fig_w, use_container_width=True)
        except Exception:
          st.info("重量數據暫無法繪製圖表。")
      with c2:
        try:
          compare_df["Rear_Wheel_Num"] = pd.to_numeric(
              compare_df["Rear_Wheel_Size"], errors="coerce"
          )
          fig_wheel = px.bar(
              compare_df,
              x="Display_Label",
              y="Rear_Wheel_Num",
              title="後輪尺寸 (直徑)",
              text="Rear_Wheel_Num",
              color="Display_Label",
          )
          st.plotly_chart(fig_wheel, use_container_width=True)
        except Exception:
          st.info("輪胎尺寸暫無法繪製圖表。")

    # 根據側邊欄設定的順序依序渲染畫面
    block_map = {
        "📷 產品外觀照片": render_photos,
        "📋 詳細規格對照表": render_table,
        "📊 關鍵規格圖表": render_charts,
    }

    for section in section_order:
      if section in block_map:
        block_map[section]()
        st.write("")  # 間隔行

# -------------------------------------------------------------
# 頁面 2: 規格總覽清單
# -------------------------------------------------------------
elif page == "📋 規格總覽清單":
  st.header("📋 所有型號規格清單")
  search_term = st.text_input(
      "🔍 搜尋型號 / 品名 / EAN：", placeholder="例如：aire twin 或 S1217"
  )
  filtered_df = df.copy()

  if search_term:
    filtered_df = filtered_df[
        filtered_df["Model_Number"]
        .str.contains(search_term, case=False, na=False)
        | filtered_df["Product_Name"].str.contains(
            search_term, case=False, na=False
        )
        | filtered_df["EAN"].astype(str).str.contains(search_term, na=False)
    ]

  st.write(f"共找到 {len(filtered_df)} 筆產品規格")
  st.dataframe(filtered_df, use_container_width=True)

# -------------------------------------------------------------
# 頁面 3: 新增 / 編輯型號
# -------------------------------------------------------------
elif page == "➕ 新增/編輯型號":
  st.header("📝 產品規格錄入 / 編輯")

  with st.form("stroller_form"):
    st.subheader("1. 基本資訊")
    col1, col2, col3 = st.columns(3)
    with col1:
      model_number = st.text_input("Model Number (必填/主鍵)*")
      product_name = st.text_input("Product Name*")
    with col2:
      item_code = st.text_input("Item Code")
      fashion = st.text_input("Fashion / 花色")
    with col3:
      ean = st.text_input("EAN Barcode")
      stroller_cat = st.selectbox(
          "類別", ["compact stroller", "double stroller", "full size", "other"]
      )

    st.subheader("2. 產品照片上傳")
    uploaded_photo = st.file_uploader(
        "選擇此型號的照片 (JPG/PNG)", type=["jpg", "png"]
    )

    st.subheader("3. 輪胎與底盤規格")
    w1, w2, w3, w4 = st.columns(4)
    with w1:
      front_wheel = st.text_input("前輪尺寸 (Front Wheel)")
    with w2:
      rear_wheel = st.text_input("後輪尺寸 (Rear Wheel)")
    with w3:
      wheel_type = st.text_input("輪胎材質/種類")
    with w4:
      suspension = st.selectbox(
          "四輪避震", ["All Wheel Suspension", "Front Suspension", "No"]
      )

    st.subheader("4. 尺寸與重量")
    d1, d2, d3, d4 = st.columns(4)
    with d1:
      weight = st.text_input("產品淨重 (kg)")
    with d2:
      basket_cap = st.text_input("置物籃承重 (kg)")
    with d3:
      one_hand = st.selectbox("單手收車 (One hand Fold)", ["yes", "no"])
    with d4:
      usage = st.text_input("適用年齡/體重")

    submitted = st.form_submit_button("💾 儲存 / 更新至資料庫")
    if submitted:
      if not model_number or not product_name:
        st.error("請填寫 Model Number 與 Product Name！")
      else:
        if uploaded_photo is not None:
          ext = uploaded_photo.name.split(".")[-1]
          with open(f"images/{model_number}.{ext}", "wb") as f:
            f.write(uploaded_photo.getbuffer())
          st.info(f"產品照片已存為 images/{model_number}.{ext}")

        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM strollers WHERE Model_Number = ?",
            (model_number,),
        )
        exists = cur.fetchone()[0] > 0
        if exists:
          cur.execute(
              """
                        UPDATE strollers SET
                            Product_Name=?, Item_Code=?, Fashion=?, EAN=?,
                            Stroller_Category=?, Front_Wheel_Size=?, Rear_Wheel_Size=?,
                            Wheel_Type=?, Wheel_Suspension=?, Product_Weight_kg=?,
                            Basket_Capacity_kg=?, One_Hand_Fold=?, Product_Usage=?
                        WHERE Model_Number=?
                    """,
              (
                  product_name,
                  item_code,
                  fashion,
                  ean,
                  stroller_cat,
                  front_wheel,
                  rear_wheel,
                  wheel_type,
                  suspension,
                  weight,
                  basket_cap,
                  one_hand,
                  usage,
                  model_number,
              ),
          )
          st.success(f"型號 {model_number} 規格與資料已更新！")
        else:
          cur.execute(
              """
                        INSERT INTO strollers (
                            Model_Number, Product_Name, Item_Code, Fashion, EAN,
                            Stroller_Category, Front_Wheel_Size, Rear_Wheel_Size,
                            Wheel_Type, Wheel_Suspension, Product_Weight_kg,
                            Basket_Capacity_kg, One_Hand_Fold, Product_Usage
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
              (
                  model_number,
                  product_name,
                  item_code,
                  fashion,
                  ean,
                  stroller_cat,
                  front_wheel,
                  rear_wheel,
                  wheel_type,
                  suspension,
                  weight,
                  basket_cap,
                  one_hand,
                  usage,
              ),
          )
          st.success(f"新推車型號 {model_number} 已成功建立！")
        conn.commit()
        conn.close()