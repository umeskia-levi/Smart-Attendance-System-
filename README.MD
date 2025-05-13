# 📚 Smart Attendance System

A dynamic, QR Code-based attendance management web app built with **Streamlit**. This application enables educational institutions or training organizers to manage student attendance manually or via QR scans, visualize attendance trends, and export attendance reports.

---

## 🚀 Features

- ✅ **Manual Attendance**: Mark students present or absent by checkbox.
- 📤 **Upload Student List**: Upload students via CSV or manually add one-by-one.
- 📱 **QR Code Attendance**: Automatically generate session-specific QR codes for student check-ins.
- 📊 **Visual Reports**: Pie charts and bar graphs for attendance statistics.
- 📄 **Exportable Data**: Export attendance data in CSV or Excel format.
- 🧠 **Session Management**: Sessions expire after one hour and track who checked in.

---

## 🖥️ Tech Stack

- **Frontend/UI**: [Streamlit](https://streamlit.io/)
- **Data Processing**: `pandas`, `numpy`
- **QR Code Generation**: `qrcode`
- **Visualization**: `plotly.express`
- **File Export**: `openpyxl`, `base64`
- **Misc**: `datetime`, `random`, `string`, `io`

---

## 📦 Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/smart-attendance-system.git
cd smart-attendance-system
