#!/usr/bin/env python3

import sys
import os
import subprocess

# Fallback clipboard function if AppKit is missing
def fallback_copy_to_clipboard(text):
    try:
        p = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
        p.communicate(input=text.encode('utf-8'))
    except Exception as e:
        print("⚠️ Could not copy error message to clipboard:", e)

# Check for PyObjC
try:
    from AppKit import NSPasteboard
    from Foundation import NSString
except ImportError:
    error_message = (
        "❌ Missing required modules: AppKit and Foundation (PyObjC)\n"
        "➡️  Install them with: pip3 install pyobjc"
    )
    print(error_message)
    fallback_copy_to_clipboard(error_message)
    sys.exit(1)


NSPasteboardTypeHTML = "public.html"
NSPasteboardTypePlainText = "public.utf8-plain-text"

def main():
    text = os.environ.get("TEXT")
    url = os.environ.get("URL")

    if not text or not url:
        print("❌ Environment variables TEXT and URL must be set.")
        return

    # Create rich HTML hyperlink and plain fallback string
    html = f'<a href="{url}">{text}</a>'
    plain = f'{text}'  # you can change this to f"[{text}]({url})" if you prefer markdown

    # Copy both HTML and plain text to the clipboard
    pb = NSPasteboard.generalPasteboard()
    pb.clearContents()
    pb.declareTypes_owner_([NSPasteboardTypeHTML, NSPasteboardTypePlainText], None)
    pb.setString_forType_(NSString.stringWithString_(html), NSPasteboardTypeHTML)
    pb.setString_forType_(NSString.stringWithString_(plain), NSPasteboardTypePlainText)

    print("✅ Copied both rich and plain text to clipboard.")

if __name__ == "__main__":
    main()
