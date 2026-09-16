import base64
from collections import defaultdict
import csv
import io
import os
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from FinMind.data import DataLoader
from bs4 import BeautifulSoup
import cv2
import ezdxf
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d import Axes3D, art3d
import mplfinance as mpf
import numpy as np
from PIL import Image, ImageTk
import requests
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from stl import mesh
from ultralytics import YOLO
import pandas as pd
import yfinance as yf

# 設定 matplotlib 支援中文
matplotlib.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei']
matplotlib.rcParams['axes.unicode_minus'] = False


# ==============================================================================
# Main Application Class (PageControl / Notebook Integration)
# ==============================================================================


class MultiToolApp:

  def __init__(self, root):
    self.root = root
    self.root.title("AI 視覺、網路爬蟲與股票分析整合系統")
    self.root.geometry("1300x900")

    # 建立 ttk.Notebook
    self.notebook = ttk.Notebook(self.root)
    self.notebook.pack(fill="both", expand=True)

    # 建立六個 Tab 頁面
    self.tab1 = ttk.Frame(self.notebook)
    self.tab2 = ttk.Frame(self.notebook)
    self.tab3 = ttk.Frame(self.notebook)
    self.tab4 = ttk.Frame(self.notebook)
    self.tab5 = ttk.Frame(self.notebook)
    self.tab6 = ttk.Frame(self.notebook)

    self.notebook.add(self.tab1, text="  Tabsheet1: 網路圖片爬蟲系統  ")
    self.notebook.add(self.tab2, text="  Tabsheet2: 偵測動態物件  ")
    self.notebook.add(self.tab3, text="  Tabsheet3: 偵測靜態物件  ")
    self.notebook.add(self.tab4, text="  Tabsheet4: 股票分析  ")
    self.notebook.add(self.tab5, text="  Tabsheet5: AutoCAD  ")
    self.notebook.add(self.tab6, text="  Tabsheet6: SolidWorks  ")

    # 初始化六個模組
    self.init_tab1()
    self.init_tab2()
    self.init_tab3()
    self.init_tab4()
    self.init_tab5()
    self.init_tab6()

  # ==========================================================================
  # Tabsheet1: 網路圖片爬蟲系統
  # ==========================================================================
  def init_tab1(self):
    tab = self.tab1
    self.t1_save_path = ""
    self.t1_tk_images = []

    tab.columnconfigure(1, weight=1)
    tab.rowconfigure(0, weight=1)

    left_frame = tk.Frame(
        tab, width=300, bd=2, relief="groove", padx=10, pady=10
    )
    left_frame.grid(row=0, column=0, sticky="nswe", padx=10, pady=10)
    left_frame.pack_propagate(False)

    tk.Label(
        left_frame, text="【輸入搜尋關鍵字】", font=("Arial", 12, "bold")
    ).pack(anchor="w", pady=(0, 5))
    self.t1_entry_keyword = tk.Entry(left_frame, font=("Arial", 11))
    self.t1_entry_keyword.pack(fill="x", pady=(0, 15))
    self.t1_entry_keyword.insert(0, "新竹職訓中心")

    lframe_count = tk.LabelFrame(
        left_frame, text="【抓取數量設定】", padx=5, pady=5
    )
    lframe_count.pack(fill="x", pady=(0, 15))

    tk.Label(
        lframe_count, text="目標張數 (預設8，最大100):", font=("Arial", 9)
    ).pack(anchor="w")
    self.t1_entry_count = tk.Entry(lframe_count, font=("Arial", 11))
    self.t1_entry_count.pack(fill="x", pady=5)
    self.t1_entry_count.insert(0, "8")

    btn_select_path = tk.Button(
        left_frame, text="選擇存照片路徑", command=self.t1_select_folder
    )
    btn_select_path.pack(fill="x", pady=5)

    lframe_path = tk.LabelFrame(
        left_frame, text="打印出選擇路徑", padx=5, pady=5
    )
    lframe_path.pack(fill="x", pady=(0, 15))
    self.t1_lbl_path = tk.Label(
        lframe_path,
        text="尚未選擇路徑...",
        fg="blue",
        wraplength=250,
        justify="left",
    )
    self.t1_lbl_path.pack(anchor="w")

    self.t1_btn_start = tk.Button(
        left_frame,
        text="開始抓取 (啟動 Edge)",
        command=self.t1_start_thread,
        bg="#4CAF50",
        fg="white",
        font=("Arial", 11, "bold"),
        height=2,
    )
    self.t1_btn_start.pack(fill="x", pady=10)

    tk.Label(left_frame, text="執行狀態:", font=("Arial", 9)).pack(
        anchor="w", pady=(5, 0)
    )
    self.t1_txt_log = scrolledtext.ScrolledText(
        left_frame, height=8, font=("Consolas", 9), state="disabled"
    )
    self.t1_txt_log.pack(fill="both", expand=True)

    right_frame = tk.Frame(tab, bd=2, relief="sunken")
    right_frame.grid(row=0, column=1, sticky="nswe", padx=10, pady=10)

    canvas = tk.Canvas(right_frame, bg="#e0e0e0")
    canvas.pack(side="left", fill="both", expand=True)

    scrollbar = tk.Scrollbar(
        right_frame, orient="vertical", command=canvas.yview
    )
    scrollbar.pack(side="right", fill="y")
    canvas.configure(yscrollcommand=scrollbar.set)

    self.t1_grid_frame = tk.Frame(canvas, bg="#e0e0e0")
    canvas.create_window((0, 0), window=self.t1_grid_frame, anchor="nw")
    self.t1_grid_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
    )

    self.t1_grid_columns = 3
    self.t1_current_img_index = 0

  def t1_log(self, msg):
    self.t1_txt_log.configure(state="normal")
    self.t1_txt_log.insert(tk.END, msg + "\n")
    self.t1_txt_log.see(tk.END)
    self.t1_txt_log.configure(state="disabled")
    self.root.update_idletasks()

  def t1_select_folder(self):
    path = filedialog.askdirectory()
    if path:
      self.t1_save_path = path
      self.t1_lbl_path.config(text=os.path.normpath(path), fg="black")
      self.t1_log(f"-> 已選擇儲存路徑: {path}")

  def t1_add_image(self, img_data):
    try:
      image = Image.open(io.BytesIO(img_data))
      image.thumbnail((250, 250))
      tk_img = ImageTk.PhotoImage(image)
      self.t1_tk_images.append(tk_img)

      row = self.t1_current_img_index // self.t1_grid_columns
      col = self.t1_current_img_index % self.t1_grid_columns

      f_single = tk.Frame(self.t1_grid_frame, bd=1, relief="solid", bg="white")
      f_single.grid(row=row, column=col, padx=10, pady=10, sticky="nesw")

      lbl_img = tk.Label(f_single, image=tk_img, bg="white")
      lbl_img.pack(pady=5)
      lbl_num = tk.Label(
          f_single,
          text=f"圖片 {self.t1_current_img_index + 1}",
          font=("Arial", 9),
          bg="white",
      )
      lbl_num.pack(pady=(0, 5))

      self.t1_current_img_index += 1
      self.root.update_idletasks()
    except Exception as e:
      self.t1_log(f"Error 顯示圖片: {e}")

  def t1_start_thread(self):
    keyword = self.t1_entry_keyword.get().strip()
    count_str = self.t1_entry_count.get().strip()
    target_count = (
        int(count_str) if count_str.isdigit() and int(count_str) > 0 else 8
    )
    if target_count > 100:
      target_count = 100

    if not keyword or not self.t1_save_path:
      messagebox.showwarning("警告", "請先輸入關鍵字並選擇儲存路徑！")
      return

    self.t1_btn_start.config(state="disabled", text="正在抓取...")
    for widget in self.t1_grid_frame.winfo_children():
      widget.destroy()
    self.t1_tk_images = []
    self.t1_current_img_index = 0

    t = threading.Thread(
        target=self.t1_crawler_process,
        args=(keyword, self.t1_save_path, target_count),
    )
    t.daemon = True
    t.start()

  def t1_crawler_process(self, search_query, target_folder, target_count):
    self.t1_log(f"=== 爬蟲開始: {search_query} ({target_count}張) ===")
    if not os.path.exists(target_folder):
      os.makedirs(target_folder)

    edge_options = Options()
    edge_options.add_argument("--headless")
    edge_options.add_argument("--no-sandbox")
    edge_options.add_argument("--disable-dev-shm-usage")
    edge_options.add_argument("--disable-blink-features=AutomationControlled")
    edge_options.add_experimental_option(
        "excludeSwitches", ["enable-automation"]
    )
    edge_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )

    url = f"https://www.google.com/search?hl=zh-TW&tbm=isch&q={search_query}"
    try:
      driver = webdriver.Edge(options=edge_options)
    except Exception as e:
      self.t1_log(f"錯誤: 無法啟動 Edge ({e})")
      self.root.after(
          0,
          lambda: self.t1_btn_start.config(
              state="normal", text="開始抓取 (啟動 Edge)"
          ),
      )
      return

    try:
      driver.get(url)
      time.sleep(2)
      images_srcs = set()
      scroll_attempts = 0

      while len(images_srcs) < (target_count * 1.5) and scroll_attempts < 15:
        driver.execute_script(
            "window.scrollTo(0, document.documentElement.scrollHeight);"
        )
        time.sleep(1.5)
        scroll_attempts += 1
        soup = BeautifulSoup(driver.page_source, "html.parser")
        for img in soup.find_all("img"):
          src = (
              img.get("src")
              or img.get("data-src")
              or img.get("data-deferred-src")
          )
          if src and (
              (src.startswith("data:image") and len(src) > 1000)
              or (src.startswith("http") and "google.com" not in src)
          ):
            images_srcs.add(src)

      saved_count = 0
      for img_src in images_srcs:
        if saved_count >= target_count:
          break
        try:
          if img_src.startswith("data:image"):
            img_data = base64.b64decode(img_src.split(",", 1)[1])
          else:
            res = requests.get(img_src, timeout=5)
            img_data = res.content if res.status_code == 200 else None

          if img_data and len(img_data) >= 3072:
            file_name = os.path.join(
                target_folder,
                f"{search_query}_{str(saved_count+1).zfill(3)}.jpg",
            )
            with open(file_name, "wb") as f:
              f.write(img_data)
            saved_count += 1
            self.t1_log(
                f"[{saved_count}/{target_count}] 已存:"
                f" {os.path.basename(file_name)}"
            )
            self.root.after(0, self.t1_add_image, img_data)
        except Exception:
          pass
      self.t1_log(f"=== 下載完成，共儲存 {saved_count} 張圖片 ===")
    finally:
      driver.quit()
      self.root.after(
          0,
          lambda: self.t1_btn_start.config(
              state="normal", text="開始抓取 (啟動 Edge)"
          ),
      )

  # ==========================================================================
  # Tabsheet2: 偵測動態物件 (YOLOv8 影片分析)
  # ==========================================================================
  def init_tab2(self):
    tab = self.tab2
    self.t2_video_path = ""
    self.t2_output_path = ""
    self.t2_is_running = False
    self.t2_is_paused = False

    tab.columnconfigure(1, weight=1)
    tab.rowconfigure(0, weight=1)

    left_frame = tk.Frame(
        tab, width=300, bd=2, relief="groove", padx=10, pady=10
    )
    left_frame.grid(row=0, column=0, sticky="nswe", padx=10, pady=10)
    left_frame.pack_propagate(False)

    btn_select_video = tk.Button(
        left_frame, text="選擇影片檔案", command=self.t2_select_video
    )
    btn_select_video.pack(fill="x", pady=3)

    lframe_video = tk.LabelFrame(
        left_frame, text="選擇的影片路徑", padx=5, pady=3
    )
    lframe_video.pack(fill="x", pady=(0, 5))
    self.t2_lbl_video = tk.Label(
        lframe_video,
        text="尚未選擇影片...",
        fg="blue",
        wraplength=250,
        justify="left",
    )
    self.t2_lbl_video.pack(anchor="w")

    btn_select_out = tk.Button(
        left_frame, text="選擇輸出路徑", command=self.t2_select_output_folder
    )
    btn_select_out.pack(fill="x", pady=3)

    lframe_out = tk.LabelFrame(left_frame, text="選擇的輸出路徑", padx=5, pady=3)
    lframe_out.pack(fill="x", pady=(0, 5))
    self.t2_lbl_output = tk.Label(
        lframe_out,
        text="尚未選擇輸出路徑...",
        fg="blue",
        wraplength=250,
        justify="left",
    )
    self.t2_lbl_output.pack(anchor="w")

    self.t2_btn_start = tk.Button(
        left_frame,
        text="開始偵測 (YOLOv8)",
        command=self.t2_start_thread,
        bg="#2196F3",
        fg="white",
        font=("Arial", 11, "bold"),
        height=2,
    )
    self.t2_btn_start.pack(fill="x", pady=(5, 3))

    self.t2_btn_pause = tk.Button(
        left_frame,
        text="暫停偵測",
        command=self.t2_toggle_pause,
        bg="#FFC107",
        fg="black",
        font=("Arial", 10, "bold"),
        state="disabled",
    )
    self.t2_btn_pause.pack(fill="x", pady=2)

    self.t2_btn_stop = tk.Button(
        left_frame,
        text="停止偵測",
        command=self.t2_stop_detection,
        bg="#F44336",
        fg="white",
        font=("Arial", 10, "bold"),
        state="disabled",
    )
    self.t2_btn_stop.pack(fill="x", pady=(2, 5))

    tk.Label(left_frame, text="執行狀態與數據分析:", font=("Arial", 9)).pack(
        anchor="w", pady=(3, 0)
    )
    self.t2_txt_log = scrolledtext.ScrolledText(
        left_frame, height=8, font=("Consolas", 9), state="disabled"
    )
    self.t2_txt_log.pack(fill="both", expand=True)

    right_frame = tk.Frame(tab, bd=2, relief="sunken")
    right_frame.grid(row=0, column=1, sticky="nswe", padx=10, pady=10)

    self.t2_canvas = tk.Canvas(right_frame, bg="#333333")
    self.t2_canvas.pack(side="left", fill="both", expand=True)

    scrollbar = tk.Scrollbar(
        right_frame, orient="vertical", command=self.t2_canvas.yview
    )
    scrollbar.pack(side="right", fill="y")
    self.t2_canvas.configure(yscrollcommand=scrollbar.set)

    self.t2_lbl_display = tk.Label(self.t2_canvas, bg="#333333")
    self.t2_canvas.create_window(
        (0, 0), window=self.t2_lbl_display, anchor="nw"
    )

  def t2_log(self, msg):
    self.t2_txt_log.configure(state="normal")
    self.t2_txt_log.insert(tk.END, msg + "\n")
    self.t2_txt_log.see(tk.END)
    self.t2_txt_log.configure(state="disabled")
    self.root.update_idletasks()

  def t2_get_safe_folder(self, folder_path):
    drive, tail = os.path.splitdrive(folder_path)
    if tail in ["\\", "/", ""]:
      safe_path = os.path.join(folder_path, "output_results")
      os.makedirs(safe_path, exist_ok=True)
      return safe_path
    return folder_path

  def t2_select_video(self):
    path = filedialog.askopenfilename(
        filetypes=[("Video Files", "*.mp4 *.avi *.mov *.mkv")]
    )
    if path:
      self.t2_video_path = path
      self.t2_lbl_video.config(text=os.path.normpath(path), fg="black")
      self.t2_log(f"-> 已選擇影片: {path}")

      default_dir = self.t2_get_safe_folder(os.path.dirname(path))
      self.t2_output_path = default_dir
      self.t2_lbl_output.config(text=os.path.normpath(default_dir), fg="black")

  def t2_select_output_folder(self):
    path = filedialog.askdirectory()
    if path:
      safe_path = self.t2_get_safe_folder(path)
      self.t2_output_path = safe_path
      self.t2_lbl_output.config(text=os.path.normpath(safe_path), fg="black")
      self.t2_log(f"-> 已選擇輸出路徑: {safe_path}")

  def t2_toggle_pause(self):
    if not self.t2_is_running:
      return
    self.t2_is_paused = not self.t2_is_paused
    if self.t2_is_paused:
      self.t2_btn_pause.config(text="繼續偵測", bg="#4CAF50", fg="white")
      self.t2_log("⏸️ 影片已暫停。")
    else:
      self.t2_btn_pause.config(text="暫停偵測", bg="#FFC107", fg="black")
      self.t2_log("▶️ 影片繼續播放...")

  def t2_stop_detection(self):
    if self.t2_is_running:
      self.t2_is_running = False
      self.t2_is_paused = False
      self.t2_log("⏹️ 正在停止偵測...")

  def t2_start_thread(self):
    if not self.t2_video_path or not os.path.exists(self.t2_video_path):
      messagebox.showwarning("警告", "請先選擇有效的影片檔案！")
      return

    if not self.t2_output_path:
      default_dir = self.t2_get_safe_folder(
          os.path.dirname(self.t2_video_path)
      )
      self.t2_output_path = default_dir
      self.t2_lbl_output.config(text=os.path.normpath(default_dir), fg="black")

    self.t2_btn_start.config(state="disabled", text="偵測進行中...")
    self.t2_btn_pause.config(
        state="normal", text="暫停偵測", bg="#FFC107", fg="black"
    )
    self.t2_btn_stop.config(state="normal")

    self.t2_is_running = True
    self.t2_is_paused = False

    t = threading.Thread(target=self.t2_process_video)
    t.daemon = True
    t.start()

  def t2_process_video(self):
    self.t2_log("🚀 正在載入 YOLOv8 模型...")
    try:
      model = YOLO("yolov8n.pt")
    except Exception as e:
      self.t2_log(f"❌ 模型載入失敗: {e}")
      self.root.after(0, self.t2_reset_buttons)
      return

    cap = cv2.VideoCapture(self.t2_video_path)
    width = int(cap.get(3))
    height = int(cap.get(4))
    fps = int(cap.get(5)) or 30

    os.makedirs(self.t2_output_path, exist_ok=True)

    out_video_file = os.path.join(self.t2_output_path, "output.mp4")
    out_csv_file = os.path.join(self.t2_output_path, "detections.csv")

    writer = cv2.VideoWriter(
        out_video_file, cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height)
    )

    try:
      csv_file = open(out_csv_file, "w", newline="")
      csv_writer = csv.writer(csv_file)
      csv_writer.writerow(["Frame", "Class", "Confidence"])
    except Exception as e:
      self.t2_log(f"❌ 無法建立 CSV 檔案 ({e})")
      self.root.after(0, self.t2_reset_buttons)
      return

    total_frames = 0
    total_objects = 0
    class_counter = defaultdict(int)
    start_time = time.time()

    self.t2_log("🎬 開始處理影片...")

    while cap.isOpened() and self.t2_is_running:
      while self.t2_is_paused and self.t2_is_running:
        time.sleep(0.1)

      if not self.t2_is_running:
        break

      success, frame = cap.read()
      if not success:
        break

      total_frames += 1
      results = model.predict(frame, conf=0.5, verbose=False)
      boxes = results[0].boxes

      for box in boxes:
        cls = int(box.cls[0])
        conf = float(box.conf[0])
        class_name = model.names[cls]

        class_counter[class_name] += 1
        total_objects += 1
        csv_writer.writerow([total_frames, class_name, round(conf, 2)])

      annotated = results[0].plot()

      fps_live = total_frames / (time.time() - start_time)
      cv2.putText(
          annotated,
          f"FPS: {fps_live:.1f}",
          (20, 40),
          cv2.FONT_HERSHEY_SIMPLEX,
          1,
          (0, 255, 0),
          2,
      )
      cv2.putText(
          annotated,
          f"Objects: {len(boxes)}",
          (20, 80),
          cv2.FONT_HERSHEY_SIMPLEX,
          1,
          (255, 0, 0),
          2,
      )

      writer.write(annotated)

      canvas_w = self.t2_canvas.winfo_width()
      if canvas_w < 50:
        canvas_w = 750

      target_w = canvas_w - 5
      target_h = int(target_w * (height / width))

      rgb_img = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
      pil_img = Image.fromarray(rgb_img)
      pil_img = pil_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
      tk_img = ImageTk.PhotoImage(pil_img)

      self.root.after(0, self.t2_update_display, tk_img)
      time.sleep(0.01)

    cap.release()
    writer.release()
    csv_file.close()

    if not self.t2_is_running:
      self.t2_log("\n⏹️ 使用者手動停止偵測。")
    else:
      self.t2_log("\n=== 影片播放與偵測完成 ===")

    self.t2_log("========== 偵測報告 ==========")
    self.t2_log(f"處理總影格數: {total_frames}")
    self.t2_log(f"偵測物件總數: {total_objects}")
    for cls, count in sorted(class_counter.items()):
      self.t2_log(f" - {cls}: {count}")
    self.t2_log(f"已匯出影片: {out_video_file}")
    self.t2_log(f"已匯出 CSV: {out_csv_file}")

    self.root.after(0, self.t2_reset_buttons)

  def t2_reset_buttons(self):
    self.t2_btn_start.config(state="normal", text="開始偵測 (YOLOv8)")
    self.t2_btn_pause.config(
        state="disabled", text="暫停偵測", bg="#FFC107", fg="black"
    )
    self.t2_btn_stop.config(state="disabled")
    self.t2_is_running = False
    self.t2_is_paused = False

  def t2_update_display(self, tk_img):
    self.t2_lbl_display.config(image=tk_img)
    self.t2_lbl_display.image = tk_img
    self.t2_canvas.configure(scrollregion=self.t2_canvas.bbox("all"))

  # ==========================================================================
  # Tabsheet3: 偵測靜態物件 (YOLOv8 自動物件偵測)
  # ==========================================================================
  def init_tab3(self):
    tab = self.tab3
    self.t3_img_path = ""
    self.t3_output_path = ""

    tab.columnconfigure(1, weight=1)
    tab.rowconfigure(0, weight=1)

    left_frame = tk.Frame(
        tab, width=300, bd=2, relief="groove", padx=10, pady=10
    )
    left_frame.grid(row=0, column=0, sticky="nswe", padx=10, pady=10)
    left_frame.pack_propagate(False)

    btn_select_img = tk.Button(
        left_frame, text="選擇圖片檔案", command=self.t3_select_image
    )
    btn_select_img.pack(fill="x", pady=3)

    lframe_img = tk.LabelFrame(
        left_frame, text="選擇的圖片路徑", padx=5, pady=3
    )
    lframe_img.pack(fill="x", pady=(0, 5))
    self.t3_lbl_img = tk.Label(
        lframe_img,
        text="尚未選擇圖片...",
        fg="blue",
        wraplength=250,
        justify="left",
    )
    self.t3_lbl_img.pack(anchor="w")

    btn_select_out = tk.Button(
        left_frame, text="選擇輸出路徑", command=self.t3_select_output_folder
    )
    btn_select_out.pack(fill="x", pady=3)

    lframe_out = tk.LabelFrame(left_frame, text="選擇的輸出路徑", padx=5, pady=3)
    lframe_out.pack(fill="x", pady=(0, 5))
    self.t3_lbl_output = tk.Label(
        lframe_out,
        text="尚未選擇輸出路徑...",
        fg="blue",
        wraplength=250,
        justify="left",
    )
    self.t3_lbl_output.pack(anchor="w")

    tk.Label(
        left_frame, text="偵測物件種類 (YOLOv8 模型選擇):", font=("Arial", 9, "bold")
    ).pack(anchor="w", pady=(5, 2))

    self.t3_combo_model = ttk.Combobox(
        left_frame,
        values=[
            "多類別自動偵測 (yolov8x-oiv7.pt - 600類:人/水果/物質)",
            "自動物件偵測 (yolov8n.pt - 80類)",
            "網格細分分類 (yolov8n-cls.pt)",
        ],
        state="readonly",
    )
    self.t3_combo_model.current(0)
    self.t3_combo_model.pack(fill="x", pady=(0, 5))

    frame_conf = tk.Frame(left_frame)
    frame_conf.pack(fill="x", pady=2)

    tk.Label(
        frame_conf, text="信心度門檻 (Conf):", font=("Arial", 9, "bold")
    ).pack(side="left")
    self.t3_scale_conf = tk.Scale(
        frame_conf,
        from_=0.10,
        to=0.90,
        resolution=0.05,
        orient="horizontal",
        length=120,
    )
    self.t3_scale_conf.set(0.4)
    self.t3_scale_conf.pack(side="right")

    frame_grid_size = tk.Frame(left_frame)
    frame_grid_size.pack(fill="x", pady=2)

    tk.Label(frame_grid_size, text="網格列數(R):", font=("Arial", 9)).pack(
        side="left"
    )
    self.t3_spin_rows = tk.Spinbox(
        frame_grid_size, from_=1, to=10, width=3, justify="center"
    )
    self.t3_spin_rows.delete(0, "end")
    self.t3_spin_rows.insert(0, "4")
    self.t3_spin_rows.pack(side="left", padx=(2, 8))

    tk.Label(frame_grid_size, text="網格欄數(C):", font=("Arial", 9)).pack(
        side="left"
    )
    self.t3_spin_cols = tk.Spinbox(
        frame_grid_size, from_=1, to=10, width=3, justify="center"
    )
    self.t3_spin_cols.delete(0, "end")
    self.t3_spin_cols.insert(0, "5")
    self.t3_spin_cols.pack(side="left", padx=2)

    self.t3_btn_start = tk.Button(
        left_frame,
        text="開始偵測分析",
        command=self.t3_start_thread,
        bg="#FF9800",
        fg="white",
        font=("Arial", 11, "bold"),
        height=2,
    )
    self.t3_btn_start.pack(fill="x", pady=10)

    tk.Label(left_frame, text="執行狀態:", font=("Arial", 9)).pack(
        anchor="w", pady=(5, 0)
    )
    self.t3_txt_log = scrolledtext.ScrolledText(
        left_frame, height=8, font=("Consolas", 9), state="disabled"
    )
    self.t3_txt_log.pack(fill="both", expand=True)

    right_frame = tk.Frame(tab, bd=2, relief="sunken")
    right_frame.grid(row=0, column=1, sticky="nswe", padx=10, pady=10)

    self.t3_canvas = tk.Canvas(right_frame, bg="#e0e0e0")
    self.t3_canvas.pack(side="left", fill="both", expand=True)

    scrollbar = tk.Scrollbar(
        right_frame, orient="vertical", command=self.t3_canvas.yview
    )
    scrollbar.pack(side="right", fill="y")
    self.t3_canvas.configure(yscrollcommand=scrollbar.set)

    self.t3_lbl_display = tk.Label(self.t3_canvas, bg="#e0e0e0")
    self.t3_canvas.create_window(
        (0, 0), window=self.t3_lbl_display, anchor="nw"
    )

  def t3_log(self, msg):
    self.t3_txt_log.configure(state="normal")
    self.t3_txt_log.insert(tk.END, msg + "\n")
    self.t3_txt_log.see(tk.END)
    self.t3_txt_log.configure(state="disabled")
    self.root.update_idletasks()

  def t3_get_safe_folder(self, folder_path):
    drive, tail = os.path.splitdrive(folder_path)
    if tail in ["\\", "/", ""]:
      safe_path = os.path.join(folder_path, "output_results")
      os.makedirs(safe_path, exist_ok=True)
      return safe_path
    return folder_path

  def t3_select_image(self):
    path = filedialog.askopenfilename(
        filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp")]
    )
    if path:
      self.t3_img_path = path
      self.t3_lbl_img.config(text=os.path.normpath(path), fg="black")
      self.t3_log(f"-> 已選擇圖片: {path}")

      default_dir = self.t3_get_safe_folder(os.path.dirname(path))
      self.t3_output_path = default_dir
      self.t3_lbl_output.config(text=os.path.normpath(default_dir), fg="black")

  def t3_select_output_folder(self):
    path = filedialog.askdirectory()
    if path:
      safe_path = self.t3_get_safe_folder(path)
      self.t3_output_path = safe_path
      self.t3_lbl_output.config(text=os.path.normpath(safe_path), fg="black")
      self.t3_log(f"-> 已選擇輸出路徑: {safe_path}")

  def t3_start_thread(self):
    if not self.t3_img_path or not os.path.exists(self.t3_img_path):
      messagebox.showwarning("警告", "請先選擇有效的圖片檔案！")
      return

    if not self.t3_output_path:
      default_dir = self.t3_get_safe_folder(os.path.dirname(self.t3_img_path))
      self.t3_output_path = default_dir
      self.t3_lbl_output.config(text=os.path.normpath(default_dir), fg="black")

    self.t3_btn_start.config(state="disabled", text="分析進行中...")
    t = threading.Thread(target=self.t3_process_image)
    t.daemon = True
    t.start()

  def t3_process_image(self):
    if not self.t3_img_path or not os.path.exists(self.t3_img_path):
      self.t3_log("⚠️ 請先選擇有效的圖片檔案！")
      self.root.after(
          0,
          lambda: self.t3_btn_start.config(
              state="normal", text="開始偵測分析"
          ),
      )
      return

    try:
      img = cv2.imread(self.t3_img_path)
      if img is None:
        self.t3_log("❌ 無法讀取圖片檔案")
        return

      h, w, _ = img.shape
      selected_mode = self.t3_combo_model.get()
      user_conf = self.t3_scale_conf.get()

      if "yolov8x-oiv7.pt" in selected_mode:
        self.t3_log(
            f"🚀 載入 Open Images V7 模型 (yolov8x-oiv7.pt) | 門檻:"
            f" {user_conf}..."
        )
        model = YOLO("yolov8x-oiv7.pt")
        results = model(self.t3_img_path, conf=user_conf)
        display_img = results[0].plot()
        save_filename = "output_detection_oiv7.jpg"

      elif "yolov8n.pt" in selected_mode:
        self.t3_log(
            "🚀 載入 YOLOv8 通用物件偵測模型 (yolov8n.pt) | 門檻:"
            f" {user_conf}..."
        )
        model = YOLO("yolov8n.pt")
        results = model(self.t3_img_path, conf=user_conf)
        display_img = results[0].plot()
        save_filename = "output_detection.jpg"

      elif "yolov8n-cls.pt" in selected_mode:
        self.t3_log(
            "🧩 載入 YOLOv8-cls 圖片分類模型 (yolov8n-cls.pt) | 門檻:"
            f" {user_conf}..."
        )
        model = YOLO("yolov8n-cls.pt")

        try:
          rows = int(self.t3_spin_rows.get())
          cols = int(self.t3_spin_cols.get())
        except ValueError:
          rows, cols = 4, 5

        self.t3_log(f"✂️ 開始進行 {rows}x{cols} 網格裁切與細分類別辨識...")

        display_img = img.copy()
        cell_h, cell_w = h // rows, w // cols
        font_scale = max(0.4, w / 1500)
        thickness = max(1, int(w / 800))

        for r in range(rows):
          for c in range(cols):
            y1, y2 = r * cell_h, (r + 1) * cell_h
            x1, x2 = c * cell_w, (c + 1) * cell_w

            crop_img = img[y1:y2, x1:x2]
            results = model(crop_img, verbose=False)

            top1_idx = results[0].probs.top1
            top1_conf = results[0].probs.top1conf.item()
            label_name = results[0].names[top1_idx]

            if top1_conf >= user_conf:
              text = f"{label_name} {top1_conf * 100:.0f}%"
              text_color = (0, 255, 0)
            else:
              text = f"? {label_name} ({top1_conf * 100:.0f}%)"
              text_color = (0, 165, 255)

            cv2.rectangle(
                display_img, (x1, y1), (x2, y2), (255, 150, 0), thickness
            )
            (text_w, text_h), baseline = cv2.getTextSize(
                text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness
            )
            cv2.rectangle(
                display_img,
                (x1 + 5, y1 + 5),
                (x1 + 10 + text_w, y1 + 10 + text_h + baseline),
                (0, 0, 0),
                -1,
            )
            cv2.putText(
                display_img,
                text,
                (x1 + 8, y1 + 5 + text_h),
                cv2.FONT_HERSHEY_SIMPLEX,
                font_scale,
                text_color,
                thickness,
                cv2.LINE_AA,
            )

        save_filename = "output_classification.jpg"

      os.makedirs(self.t3_output_path, exist_ok=True)
      out_img_file = os.path.join(self.t3_output_path, save_filename)
      cv2.imwrite(out_img_file, display_img)
      self.t3_log(f"💾 已將辨識圖片儲存至: {out_img_file}")

      canvas_w = self.t3_canvas.winfo_width()
      if canvas_w < 50:
        canvas_w = 750

      target_w = canvas_w - 10
      target_h = int(target_w * (h / w))

      rgb_img = cv2.cvtColor(display_img, cv2.COLOR_BGR2RGB)
      pil_img = Image.fromarray(rgb_img)
      pil_img = pil_img.resize((target_w, target_h), Image.Resampling.LANCZOS)

      tk_img = ImageTk.PhotoImage(pil_img)
      self.root.after(0, self.t3_update_display, tk_img)
      self.t3_log("✅ 分析完成，更新預覽中！")

    except Exception as e:
      self.t3_log(f"❌ 分析過程出錯: {e}")

    finally:
      self.root.after(
          0,
          lambda: self.t3_btn_start.config(
              state="normal", text="開始偵測分析"
          ),
      )

  def t3_update_display(self, tk_img):
    self.t3_lbl_display.config(image=tk_img)
    self.t3_lbl_display.image = tk_img
    self.t3_canvas.configure(scrollregion=self.t3_canvas.bbox("all"))

  # ==========================================================================
  # Tabsheet4: 股票分析
  # ==========================================================================
  def init_tab4(self):
    self.dl = DataLoader()
    tab = self.tab4
    self.t4_canvas_widget = None

    tab.columnconfigure(1, weight=1)
    tab.rowconfigure(0, weight=1)

    left_frame = tk.Frame(
        tab, width=320, bd=2, relief="groove", padx=10, pady=10
    )
    left_frame.grid(row=0, column=0, sticky="nswe", padx=10, pady=10)
    left_frame.pack_propagate(False)

    lframe_stock = tk.LabelFrame(
        left_frame,
        text="【輸入股號或股名】",
        font=("Arial", 11, "bold"),
        padx=5,
        pady=5,
    )
    lframe_stock.pack(fill="x", pady=(0, 10))

    self.t4_entry_stock = tk.Entry(lframe_stock, font=("Arial", 11))
    self.t4_entry_stock.pack(fill="x", pady=5)
    self.t4_entry_stock.insert(0, "2330")

    lframe_kperiod = tk.LabelFrame(
        left_frame,
        text="【Combobox0: 週期選單】",
        font=("Arial", 10),
        padx=5,
        pady=5,
    )
    lframe_kperiod.pack(fill="x", pady=(0, 10))

    kperiod_options = ["日線", "1分", "5分", "15分", "30分", "60分", "周線", "月線"]
    self.t4_cb0 = ttk.Combobox(
        lframe_kperiod, values=kperiod_options, state="readonly"
    )
    self.t4_cb0.pack(fill="x", pady=2)
    self.t4_cb0.current(0)

    indicator_options = [
        "VOL(成交量)",
        "KD",
        "MACD",
        "外資",
        "投信",
        "法人",
        "融資餘額",
        "融券餘額",
    ]

    lframe_sub1 = tk.LabelFrame(
        left_frame,
        text="【Combobox1: 副圖1指標】",
        font=("Arial", 10),
        padx=5,
        pady=5,
    )
    lframe_sub1.pack(fill="x", pady=(0, 10))

    self.t4_cb1 = ttk.Combobox(
        lframe_sub1, values=indicator_options, state="readonly"
    )
    self.t4_cb1.pack(fill="x", pady=2)
    self.t4_cb1.current(0)

    lframe_sub2 = tk.LabelFrame(
        left_frame,
        text="【Combobox2: 副圖2指標】",
        font=("Arial", 10),
        padx=5,
        pady=5,
    )
    lframe_sub2.pack(fill="x", pady=(0, 10))

    self.t4_cb2 = ttk.Combobox(
        lframe_sub2, values=indicator_options, state="readonly"
    )
    self.t4_cb2.pack(fill="x", pady=2)
    self.t4_cb2.current(3)

    self.t4_btn_draw = tk.Button(
        left_frame,
        text="📈 開始分析與繪圖",
        command=self.t4_start_thread,
        bg="#009688",
        fg="white",
        font=("Arial", 11, "bold"),
        height=2,
    )
    self.t4_btn_draw.pack(fill="x", pady=10)

    tk.Label(left_frame, text="分析狀態與訊息 Log:", font=("Arial", 9)).pack(
        anchor="w", pady=(5, 0)
    )
    self.t4_txt_log = scrolledtext.ScrolledText(
        left_frame, height=8, font=("Consolas", 9), state="disabled"
    )
    self.t4_txt_log.pack(fill="both", expand=True)

    self.t4_right_frame = tk.Frame(tab, bd=2, relief="sunken", bg="white")
    self.t4_right_frame.grid(row=0, column=1, sticky="nswe", padx=10, pady=10)

  def t4_log(self, msg):
    self.t4_txt_log.configure(state="normal")
    self.t4_txt_log.insert(tk.END, msg + "\n")
    self.t4_txt_log.see(tk.END)
    self.t4_txt_log.configure(state="disabled")
    self.root.update_idletasks()

  def t4_start_thread(self):
    stock_code = self.t4_entry_stock.get().strip()
    if not stock_code:
      messagebox.showwarning("警告", "請輸入股票代碼！")
      return

    self.t4_btn_draw.config(state="disabled", text="下載數據與繪圖中...")
    t = threading.Thread(target=self.t4_draw_chart)
    t.daemon = True
    t.start()

  def t4_calculate_kd(self, df, n=9):
    low_list = df["Low"].rolling(n, min_periods=1).min()
    high_list = df["High"].rolling(n, min_periods=1).max()
    rsv = (df["Close"] - low_list) / (high_list - low_list) * 100

    k, d = [50.0], [50.0]
    for i in range(1, len(df)):
      curr_rsv = rsv.iloc[i] if not np.isnan(rsv.iloc[i]) else 50.0
      curr_k = (2 / 3) * k[-1] + (1 / 3) * curr_rsv
      curr_d = (2 / 3) * d[-1] + (1 / 3) * curr_k
      k.append(curr_k)
      d.append(curr_d)

    df["K"] = k
    df["D"] = d
    return df

  def t4_fetch_chip_data(self, clean_stock_id, start_date, end_date):
    chip_summary = pd.DataFrame()
    try:
      if hasattr(self.dl, "taiwan_stock_institutional_investors"):
        df_chip = self.dl.taiwan_stock_institutional_investors(
            stock_id=clean_stock_id, start_date=start_date, end_date=end_date
        )
      else:
        df_chip = self.dl.get_data(
            dataset="TaiwanStockInstitutionalInvestorsBuySell",
            data_id=clean_stock_id,
            start_date=start_date,
            end_date=end_date,
        )

      if not df_chip.empty:
        if "buy_sell" in df_chip.columns:
          df_chip["net_buy"] = df_chip["buy_sell"]
        elif "buy" in df_chip.columns and "sell" in df_chip.columns:
          df_chip["net_buy"] = df_chip["buy"] - df_chip["sell"]
        else:
          df_chip["net_buy"] = 0

        foreign = df_chip[df_chip["name"] == "Foreign_Investor"].groupby(
            "date"
        )["net_buy"].sum()
        investment_trust = df_chip[
            df_chip["name"] == "Investment_Trust"
        ].groupby("date")["net_buy"].sum()
        total_inst = df_chip.groupby("date")["net_buy"].sum()

        chip_summary["外資"] = foreign / 1000
        chip_summary["投信"] = investment_trust / 1000
        chip_summary["法人"] = total_inst / 1000

      if hasattr(self.dl, "taiwan_stock_margin_purchase_short_sale"):
        df_margin = self.dl.taiwan_stock_margin_purchase_short_sale(
            stock_id=clean_stock_id, start_date=start_date, end_date=end_date
        )
      else:
        df_margin = self.dl.get_data(
            dataset="TaiwanStockMarginPurchaseShortSale",
            data_id=clean_stock_id,
            start_date=start_date,
            end_date=end_date,
        )

      if not df_margin.empty:
        margin_col = next(
            (
                c
                for c in [
                    "MarginPurchaseTodayBalance",
                    "MarginPurchaseBalance",
                ]
                if c in df_margin.columns
            ),
            None,
        )
        short_col = next(
            (
                c
                for c in ["ShortSaleTodayBalance", "ShortSaleBalance"]
                if c in df_margin.columns
            ),
            None,
        )

        if margin_col:
          chip_summary["融資餘額"] = df_margin.groupby("date")[
              margin_col
          ].sum()
        if short_col:
          chip_summary["融券餘額"] = df_margin.groupby("date")[
              short_col
          ].sum()

      if not chip_summary.empty:
        chip_summary.index = pd.to_datetime(chip_summary.index)

    except Exception as e:
      self.t4_log(f"⚠️ FinMind 籌碼獲取異常: {e}")

    return chip_summary

  def t4_draw_chart(self):
      raw_stock = self.t4_entry_stock.get().strip()
      kperiod = self.t4_cb0.get()
      sub1_choice = self.t4_cb1.get()
      sub2_choice = self.t4_cb2.get()

      clean_stock = raw_stock.upper().replace(".TW", "").replace(".TWO", "")

      if not clean_stock.isdigit():
          try:
              self.t4_log(f"🔍 正在查詢名稱 [{clean_stock}] 對應的股票代碼...")
              stock_info = self.dl.get_data(dataset="TaiwanStockInfo")

              matched = stock_info[stock_info["stock_name"] == clean_stock]
              if not matched.empty:
                  clean_stock = matched.iloc[0]["stock_id"]
                  self.t4_log(f"✅ 找到對應股號: {clean_stock}")
              else:
                  fuzzy_matched = stock_info[
                      stock_info["stock_name"].str.contains(clean_stock, na=False)
                  ]
                  if not fuzzy_matched.empty:
                      clean_stock = fuzzy_matched.iloc[0]["stock_id"]
                      matched_name = fuzzy_matched.iloc[0]["stock_name"]
                      self.t4_log(f"✅ 找到相關股票: {matched_name} ({clean_stock})")
                  else:
                      self.t4_log(f"❌ 查無中文名稱 [{raw_stock}] 之股票，請確認輸入。")
                      self.root.after(
                          0,
                          lambda: self.t4_btn_draw.config(
                              state="normal", text="📈 開始分析與繪圖"
                          ),
                      )
                      return
          except Exception as e:
              self.t4_log(f"⚠️ 股票名稱查詢異常: {e}")

      target_stock = f"{clean_stock}.TW" if clean_stock.isdigit() else clean_stock

      self.t4_log(f"🚀 下載與繪製股票 [{target_stock}] 週期: {kperiod}")

      interval_map = {
          "1分": ("1m", "7d"),
          "5分": ("5m", "60d"),
          "15分": ("15m", "60d"),
          "30分": ("30m", "60d"),
          "60分": ("60m", "60d"),
          "日線": ("1d", "1y"),
          "周線": ("1wk", "2y"),
          "月線": ("1mo", "5y"),
      }
      interval, period = interval_map.get(kperiod, ("1d", "1y"))

      try:
          df = yf.download(
              target_stock,
              period=period,
              interval=interval,
              auto_adjust=False,
              prepost=True,
              progress=False,
          )

          if df.empty:
              self.t4_log(f"❌ 查無數據，請確認代碼 [{target_stock}] 是否正確。")
              self.root.after(
                  0,
                  lambda: self.t4_btn_draw.config(
                      state="normal", text="📈 開始分析與繪圖"
                  ),
              )
              return

          # 1. 扁平化 MultiIndex 欄位 (確保取到獨立欄位名)
          if isinstance(df.columns, pd.MultiIndex):
              df.columns = df.columns.get_level_values(0)

          # 2. 關鍵修正：確保 OHLCV 欄位型態為 float 並清理缺失值
          ohlc_cols = ["Open", "High", "Low", "Close"]
          for col in ohlc_cols:
              if col in df.columns:
                  df[col] = pd.to_numeric(df[col], errors="coerce")

          # 直接剔除 OHLC 含有 NaN 的列，避免 mplfinance 渲染崩潰
          df = df.dropna(subset=ohlc_cols).copy()

          if "Volume" in df.columns:
              df["Volume"] = (
                  pd.to_numeric(df["Volume"], errors="coerce").fillna(0).astype(float)
              )

          # 計算均線與指標
          df["MA5"] = df["Close"].rolling(5).mean()
          df["MA20"] = df["Close"].rolling(20).mean()
          df["MA60"] = df["Close"].rolling(60).mean()

          df["STD"] = df["Close"].rolling(20).std()
          df["Upper"] = df["MA20"] + (df["STD"] * 2)
          df["Lower"] = df["MA20"] - (df["STD"] * 2)

          exp12 = df["Close"].ewm(span=12, adjust=False).mean()
          exp26 = df["Close"].ewm(span=26, adjust=False).mean()
          df["MACD"] = exp12 - exp26
          df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
          df["Hist"] = df["MACD"] - df["Signal"]

          df = self.t4_calculate_kd(df)

          chip_options = ["外資", "投信", "法人", "融資餘額", "融券餘額"]
          need_chip = sub1_choice in chip_options or sub2_choice in chip_options

          if need_chip:
              if kperiod != "日線":
                  self.t4_log("ℹ️ 提示：籌碼面資訊（法人/融資融券）僅支援【日線】週期。")
                  for col in chip_options:
                      df[col] = 0.0
              else:
                  self.t4_log("🔍 正在從 FinMind 取得籌碼數據...")
                  start_date = df.index.min().strftime("%Y-%m-%d")
                  end_date = df.index.max().strftime("%Y-%m-%d")

                  df_chip = self.t4_fetch_chip_data(clean_stock, start_date, end_date)

                  if not df_chip.empty:
                      chip_cols = df_chip.columns
                      # 安全合併籌碼面
                      df = df.join(df_chip, how="left")
                      df[chip_cols] = df[chip_cols].fillna(0.0)
                  else:
                      self.t4_log("⚠️ 未能取回籌碼數據，預設以 0 填充。")
                      for col in chip_options:
                          df[col] = 0.0

          # 繪圖 apds 準備
          apds = [
              mpf.make_addplot(df["MA5"], color="cyan", width=0.8, label="MA5"),
              mpf.make_addplot(df["MA20"], color="magenta", width=0.8, label="MA20"),
              mpf.make_addplot(df["MA60"], color="green", width=0.8, label="MA60"),
              mpf.make_addplot(
                  df["Upper"], color="blue", alpha=0.2, label="BB Upper"
              ),
              mpf.make_addplot(
                  df["Lower"], color="blue", alpha=0.2, label="BB Lower"
              ),
          ]

          panel_ratios = [6]
          panel_counter = 1
          has_standalone_volume = False

          def setup_panel_indicator(choice, p_idx):
              nonlocal has_standalone_volume
              if choice == "VOL(成交量)":
                  has_standalone_volume = True
                  panel_ratios.append(2)

              elif choice == "KD":
                  apds.append(
                      mpf.make_addplot(
                          df["K"], color="blue", panel=p_idx, ylabel="KD", label="K(9)"
                      )
                  )
                  apds.append(
                      mpf.make_addplot(
                          df["D"], color="orange", panel=p_idx, label="D(9)"
                      )
                  )
                  panel_ratios.append(2)

              elif choice == "MACD":
                  apds.append(
                      mpf.make_addplot(
                          df["MACD"],
                          color="orange",
                          panel=p_idx,
                          ylabel="MACD",
                          label="MACD",
                      )
                  )
                  apds.append(
                      mpf.make_addplot(
                          df["Signal"], color="blue", panel=p_idx, label="Signal"
                      )
                  )
                  apds.append(
                      mpf.make_addplot(
                          df["Hist"],
                          type="bar",
                          color="gray",
                          alpha=0.5,
                          panel=p_idx,
                      )
                  )
                  panel_ratios.append(2)

              elif choice in ["外資", "投信", "法人"]:
                  vals = df.get(choice, pd.Series(0, index=df.index)).fillna(0)
                  colors = ["red" if val >= 0 else "green" for val in vals]
                  apds.append(
                      mpf.make_addplot(
                          vals,
                          type="bar",
                          color=colors,
                          panel=p_idx,
                          ylabel=f"{choice}(張)",
                      )
                  )
                  panel_ratios.append(2)

              elif choice in ["融資餘額", "融券餘額"]:
                  vals = df.get(choice, pd.Series(0, index=df.index)).fillna(0)
                  line_color = "purple" if choice == "融資餘額" else "brown"
                  apds.append(
                      mpf.make_addplot(
                          vals,
                          color=line_color,
                          panel=p_idx,
                          ylabel=f"{choice}(張)",
                      )
                  )
                  panel_ratios.append(2)

          setup_panel_indicator(sub1_choice, panel_counter)
          panel_counter += 1
          setup_panel_indicator(sub2_choice, panel_counter)

          my_color = mpf.make_marketcolors(up="r", down="g", inherit=True)
          my_style = mpf.make_mpf_style(
              marketcolors=my_color,
              rc={
                  "font.sans-serif": ["Microsoft JhengHei", "SimHei"],
                  "axes.unicode_minus": False,
                  "figure.titlesize": 16,
                  "axes.labelsize": 10,
                  "legend.fontsize": 8,
              },
          )

          self.root.after(
              0,
              self.t4_embed_chart,
              df,
              apds,
              my_style,
              target_stock,
              kperiod,
              has_standalone_volume,
              tuple(panel_ratios),
          )

      except Exception as e:
          self.t4_log(f"❌ 圖表繪製失敗: {e}")
          self.root.after(
              0,
              lambda: self.t4_btn_draw.config(
                  state="normal", text="📈 開始分析與繪圖"
              ),
          )

  def t4_embed_chart(
          self, df, apds, my_style, target_stock, kperiod, has_vol, panel_ratios
  ):
      if self.t4_canvas_widget is not None:
          self.t4_canvas_widget.get_tk_widget().destroy()

      try:
          fig, axlist = mpf.plot(
              df,
              type="candle",
              volume=has_vol,
              addplot=apds,
              figsize=(10, 6),
              style=my_style,
              title=f"\n{target_stock} 技術與籌碼分析 ({kperiod})",
              ylabel="價格 (TWD)",
              ylabel_lower="成交量",
              panel_ratios=panel_ratios,
              tight_layout=True,
              returnfig=True,
          )

          if len(axlist) > 0:
              axlist[0].legend(loc="upper left")
              ymin, ymax = axlist[0].get_ylim()
              axlist[0].set_ylim(ymin * 0.98, ymax * 1.02)

          canvas = FigureCanvasTkAgg(fig, master=self.t4_right_frame)
          canvas.draw()
          canvas.get_tk_widget().pack(fill="both", expand=True)
          self.t4_canvas_widget = canvas

          self.t4_log(f"✅ 股票 [{target_stock}] 分析圖表更新完成！")
      except Exception as e:
          self.t4_log(f"❌ 渲染 Tkinter Canvas 失敗: {e}")

      self.t4_btn_draw.config(state="normal", text="📈 開始分析與繪圖")

  # ==========================================================================
  # Tabsheet5: AutoCAD (.dxf 2D 檢視器)
  # ==========================================================================
  def init_tab5(self):
    tab = self.tab5
    self.t5_dxf_path = ""
    self.t5_canvas_widget = None

    tab.columnconfigure(1, weight=1)
    tab.rowconfigure(0, weight=1)

    # 左側控制選單區域 (按鈕與選擇檔案路徑)
    left_frame = tk.Frame(
        tab, width=300, bd=2, relief="groove", padx=10, pady=10
    )
    left_frame.grid(row=0, column=0, sticky="nswe", padx=10, pady=10)
    left_frame.pack_propagate(False)

    btn_select_dxf = tk.Button(
        left_frame, text="選擇 Auto CAD 檔案 (.dxf)", command=self.t5_select_dxf
    )
    btn_select_dxf.pack(fill="x", pady=5)

    lframe_path = tk.LabelFrame(left_frame, text="選擇檔案路徑:", padx=5, pady=5)
    lframe_path.pack(fill="x", pady=(5, 15))

    self.t5_lbl_path = tk.Label(
        lframe_path,
        text="尚未選擇檔案...",
        fg="blue",
        wraplength=250,
        justify="left",
    )
    self.t5_lbl_path.pack(anchor="w")

    # 右側 2D 圖片視窗畫布區
    self.t5_right_frame = tk.Frame(tab, bd=2, relief="sunken", bg="white")
    self.t5_right_frame.grid(row=0, column=1, sticky="nswe", padx=10, pady=10)

  def t5_select_dxf(self):
    path = filedialog.askopenfilename(
        filetypes=[("AutoCAD DXF Files", "*.dxf")]
    )
    if path:
      self.t5_dxf_path = path
      self.t5_lbl_path.config(text=os.path.normpath(path), fg="black")
      self.t5_load_and_show_dxf(path)

  def t5_load_and_show_dxf(self, file_path):
    # 若先前有渲染的圖表先清除
    if self.t5_canvas_widget is not None:
      self.t5_canvas_widget.get_tk_widget().destroy()

    try:
      # 1. 讀取 DXF 檔案[cite: 2]
      doc = ezdxf.readfile(file_path)
      msp = doc.modelspace()

      # 2. 建立 Matplotlib 2D 圖表[cite: 2]
      fig, ax = plt.subplots(figsize=(6, 6))

      # 3. 使用 ezdxf 的繪圖套件將 DXF 圖元繪製到 Matplotlib ax[cite: 2]
      ctx = RenderContext(doc)
      out = MatplotlibBackend(ax)
      Frontend(ctx, out).draw_layout(msp, finalize=True)

      # 保持長寬比一致[cite: 2]
      ax.set_aspect("equal", adjustable="datalim")

      # 4. 嵌入到 Tkinter 視窗中[cite: 2]
      canvas = FigureCanvasTkAgg(fig, master=self.t5_right_frame)
      canvas.draw()
      canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
      self.t5_canvas_widget = canvas

      # ==================================================================
      # 新增：滑鼠滾輪縮放與滑鼠拖拽平移邏輯
      # ==================================================================

      # --- 1. 滑鼠滾輪縮放事件 ---
      def on_scroll(event):
          if event.xdata is None or event.ydata is None:
              return

          # 設定縮放比例 (向上滾輪放大，向下滾輪縮小)
          base_scale = 1.25
          if event.button == 'up':
              scale_factor = 1 / base_scale
          elif event.button == 'down':
              scale_factor = base_scale
          else:
              scale_factor = 1.0

          cur_xlim = ax.get_xlim()
          cur_ylim = ax.get_ylim()

          xdata = event.xdata
          ydata = event.ydata

          new_width = (cur_xlim[1] - cur_xlim[0]) * scale_factor
          new_height = (cur_ylim[1] - cur_ylim[0]) * scale_factor

          rel_x = (cur_xlim[1] - xdata) / (cur_xlim[1] - cur_xlim[0])
          rel_y = (cur_ylim[1] - ydata) / (cur_ylim[1] - cur_ylim[0])

          ax.set_xlim([xdata - new_width * (1 - rel_x), xdata + new_width * rel_x])
          ax.set_ylim([ydata - new_height * (1 - rel_y), ydata + new_height * rel_y])

          canvas.draw_idle()

      # --- 2. 滑鼠按住中鍵/左鍵拖拽平移事件 ---
      pan_data = {'pressed': False, 'x': 0, 'y': 0}

      def on_press(event):
          if event.inaxes != ax:
              return
          # 按下滾輪(button 2)或左鍵(button 1)開始拖拽
          if event.button in (1, 2):
              pan_data['pressed'] = True
              pan_data['x'] = event.xdata
              pan_data['y'] = event.ydata

      def on_motion(event):
          if not pan_data['pressed'] or event.inaxes != ax:
              return
          if event.xdata is None or event.ydata is None:
              return

          dx = pan_data['x'] - event.xdata
          dy = pan_data['y'] - event.ydata

          cur_xlim = ax.get_xlim()
          cur_ylim = ax.get_ylim()

          ax.set_xlim(cur_xlim[0] + dx, cur_xlim[1] + dx)
          ax.set_ylim(cur_ylim[0] + dy, cur_ylim[1] + dy)

          canvas.draw_idle()

      def on_release(event):
          pan_data['pressed'] = False

      # 綁定 Matplotlib 事件監聽
      fig.canvas.mpl_connect('scroll_event', on_scroll)
      fig.canvas.mpl_connect('button_press_event', on_press)
      fig.canvas.mpl_connect('motion_notify_event', on_motion)
      fig.canvas.mpl_connect('button_release_event', on_release)

      plt.close(fig)  # 關閉避免記憶體洩漏

    except Exception as e:
        messagebox.showerror("錯誤", f"無法載入或解析 DXF 檔案:\n{e}")
  # ==========================================================================
  # Tabsheet6: SolidWorks (.stl 3D 檢視器)
  # ==========================================================================
  def init_tab6(self):
    tab = self.tab6
    self.t6_stl_path = ""
    self.t6_canvas_widget = None

    tab.columnconfigure(1, weight=1)
    tab.rowconfigure(0, weight=1)

    # 左側控制選單區域 (按鈕與選擇檔案路徑)
    left_frame = tk.Frame(
        tab, width=300, bd=2, relief="groove", padx=10, pady=10
    )
    left_frame.grid(row=0, column=0, sticky="nswe", padx=10, pady=10)
    left_frame.pack_propagate(False)

    btn_select_stl = tk.Button(
        left_frame,
        text="選擇 SolidWorks 檔案 (.stl)",
        command=self.t6_select_stl,
    )
    btn_select_stl.pack(fill="x", pady=5)

    lframe_path = tk.LabelFrame(left_frame, text="選擇檔案路徑:", padx=5, pady=5)
    lframe_path.pack(fill="x", pady=(5, 15))

    self.t6_lbl_path = tk.Label(
        lframe_path,
        text="尚未選擇檔案...",
        fg="blue",
        wraplength=250,
        justify="left",
    )
    self.t6_lbl_path.pack(anchor="w")

    # 右側 3D 播放視窗畫布區
    self.t6_right_frame = tk.Frame(tab, bd=2, relief="sunken", bg="white")
    self.t6_right_frame.grid(row=0, column=1, sticky="nswe", padx=10, pady=10)

  def t6_select_stl(self):
    path = filedialog.askopenfilename(filetypes=[("SolidWorks STL Files", "*.stl")])
    if path:
      self.t6_stl_path = path
      self.t6_lbl_path.config(text=os.path.normpath(path), fg="black")
      self.t6_load_and_show_stl(path)

  def t6_load_and_show_stl(self, file_path):
    # 若先前有渲染的圖表先清除
    if self.t6_canvas_widget is not None:
      self.t6_canvas_widget.get_tk_widget().destroy()

    try:
      # 1. 讀取 STL 模型[cite: 1]
      your_mesh = mesh.Mesh.from_file(file_path)

      # 2. 建立 Matplotlib 3D 圖表[cite: 1]
      fig = plt.figure(figsize=(6, 6))
      ax = fig.add_subplot(111, projection="3d")

      # 3. 使用 art3d.Poly3DCollection 將網格繪製於 3D 圖表上[cite: 1]
      mesh_collection = art3d.Poly3DCollection(
          your_mesh.vectors, alpha=0.6, edgecolor="k"
      )
      ax.add_collection3d(mesh_collection)

      # 自動調整 X, Y, Z 軸範圍[cite: 1]
      scale = your_mesh.points.flatten()
      ax.auto_scale_xyz(scale, scale, scale)

      # 4. 嵌入到 Tkinter 視窗中[cite: 1]
      canvas = FigureCanvasTkAgg(fig, master=self.t6_right_frame)
      canvas.draw()
      canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
      self.t6_canvas_widget = canvas
    except Exception as e:
      messagebox.showerror("錯誤", f"無法載入或解析 STL 檔案:\n{e}")


if __name__ == "__main__":
  root = tk.Tk()
  app = MultiToolApp(root)
  root.mainloop()