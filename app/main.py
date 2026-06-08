import customtkinter as ctk

from app.ui import KrleMDApp


def main():
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    app = KrleMDApp()
    app.mainloop()


if __name__ == "__main__":
    main()
