#!/usr/bin/env python3
"""
Professional Architecture Diagram Generator
Outputs:
- architecture/solution-architecture.png (High-Res 2400x1400, PIL rendering)
- architecture/solution-architecture.svg (Scalable Vector Graphics)
- architecture/solution-architecture.drawio (diagrams.net / Lucidchart XML)
"""

import os
import math
from PIL import Image, ImageDraw, ImageFont

def get_font(name_pref, size):
    font_paths = [
        f"/usr/share/fonts/truetype/dejavu/DejaVuSans-{name_pref}.ttf",
        f"/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        f"/usr/share/fonts/truetype/lato/Lato-{name_pref}.ttf",
        f"/usr/share/fonts/truetype/lato/Lato-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    ]
    for p in font_paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()

def draw_arrow(draw, start, end, color=(88, 166, 255), width=3, arrowhead_length=15):
    x1, y1 = start
    x2, y2 = end
    draw.line([start, end], fill=color, width=width)
    dx = x2 - x1
    dy = y2 - y1
    angle = math.atan2(dy, dx)
    
    # Arrowhead points
    angle1 = angle + math.pi * 5 / 6
    angle2 = angle - math.pi * 5 / 6
    
    p1 = (x2 + arrowhead_length * math.cos(angle1), y2 + arrowhead_length * math.sin(angle1))
    p2 = (x2 + arrowhead_length * math.cos(angle2), y2 + arrowhead_length * math.sin(angle2))
    
    draw.polygon([end, p1, p2], fill=color)

def draw_step_badge(draw, center, number, bg_color=(255, 153, 0), text_color=(13, 17, 23), font=None):
    cx, cy = center
    r = 16
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=bg_color)
    bbox = font.getbbox(str(number)) if font else (0, 0, 10, 14)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    draw.text((cx - w/2, cy - h/2 - 2), str(number), fill=text_color, font=font)

def generate_diagram_png():
    width, height = 2400, 1450
    img = Image.new("RGBA", (width, height), (13, 17, 23, 255))
    draw = ImageDraw.Draw(img)

    # Fonts
    font_title = get_font("Bold", 46)
    font_subtitle = get_font("Bold", 22)
    font_group = get_font("Bold", 20)
    font_card_title = get_font("Bold", 20)
    font_card_sub = get_font("Regular", 15)
    font_badge = get_font("Bold", 17)
    font_label = get_font("Bold", 16)
    font_footer = get_font("Regular", 17)

    # Color Palette
    c_bg_dark = (13, 17, 23, 255)
    c_group_bg = (22, 27, 34, 230)
    c_card_bg = (33, 38, 45, 255)
    c_accent_orange = (255, 153, 0, 255)  # AWS Orange
    c_accent_blue = (88, 166, 255, 255)   # CloudFront / Ingestion
    c_accent_green = (63, 185, 80, 255)   # S3 Storage
    c_accent_purple = (188, 140, 255, 255)# Step Functions
    c_accent_red = (248, 81, 73, 255)     # DLQ & Alarms
    c_text_bright = (240, 246, 252, 255)
    c_text_dim = (139, 148, 158, 255)

    # Header
    draw.text((width // 2 - 470, 45), "Serverless Image Processing Pipeline", fill=c_text_bright, font=font_title)
    draw.text((width // 2 - 580, 110), "AWS Solutions Architect (Associate) — Event-Driven Architecture with S3, SQS, Step Functions & CloudFront", fill=c_accent_orange, font=font_subtitle)

    # Helper: Card Drawer
    def draw_card(x, y, w, h, title, sub1="", sub2="", border_color=c_accent_blue, icon_text=""):
        draw.rounded_rectangle([x, y, x + w, y + h], radius=16, fill=c_card_bg, outline=border_color, width=2)
        if icon_text:
            draw.text((x + 20, y + 16), icon_text, fill=border_color, font=font_card_sub)
        draw.text((x + 20, y + 40), title, fill=c_text_bright, font=font_card_title)
        if sub1:
            draw.text((x + 20, y + 74), sub1, fill=border_color, font=font_card_sub)
        if sub2:
            draw.text((x + 20, y + 98), sub2, fill=c_text_dim, font=font_card_sub)

    # Helper: Group Container
    def draw_group(x, y, w, h, label, color=c_accent_blue):
        draw.rounded_rectangle([x, y, x + w, y + h], radius=20, fill=c_group_bg, outline=color, width=2)
        draw.text((x + 25, y + 20), label, fill=color, font=font_group)

    # Draw 5 Group Containers
    # Group 1: Ingestion Tier
    draw_group(60, 180, 520, 680, "1. INGESTION & SECURE UPLOAD TIER", c_accent_blue)
    # Group 2: Queue Decoupling
    draw_group(620, 180, 450, 680, "2. ASYNCHRONOUS DECOUPLING (SQS)", c_accent_orange)
    # Group 3: Step Functions Orchestration
    draw_group(1110, 180, 600, 960, "3. STEP FUNCTIONS WORKFLOW ORCHESTRATION", c_accent_purple)
    # Group 4: Storage & Edge Delivery
    draw_group(1750, 180, 590, 960, "4. PERSISTENCE & GLOBAL DELIVERY", c_accent_green)
    # Group 5: Observability & Dead-Letter Alerts
    draw_group(60, 900, 1010, 240, "5. OBSERVABILITY, RESILIENCE & DEAD-LETTER RECOVERY", c_accent_red)

    # Cards in Group 1
    draw_card(90, 250, 460, 130, "Web & Mobile Clients", "Frontend / API Consumers", "Direct S3 Upload via Pre-signed URL", c_accent_blue, "[ CLIENT ]")
    draw_card(90, 430, 460, 130, "Amazon API Gateway", "REST API: GET /upload-url", "Throttling, CORS, API Key Validation", c_accent_blue, "[ API GATEWAY ]")
    draw_card(90, 610, 460, 130, "Presigned URL Lambda", "Python 3.12 Runtime", "Generates Time-Limited S3 PUT URL", c_accent_orange, "[ AWS LAMBDA ]")
    draw_card(90, 770, 460, 70, "Amazon S3 Source Bucket", "Raw Image Ingestion (s3://raw-images)", "Event Notification Trigger", c_accent_green, "[ S3 BUCKET ]")

    # Cards in Group 2
    draw_card(650, 260, 390, 150, "Amazon SQS Queue", "Decouples Uploads from Pipeline", "Batching, Retries (Visibility Timeout: 300s)", c_accent_orange, "[ AMAZON SQS ]")
    draw_card(650, 460, 390, 150, "Queue Consumer Lambda", "Event Source Mapping: Batch Size = 5", "Triggers Step Functions Execution", c_accent_orange, "[ AWS LAMBDA ]")
    draw_card(650, 660, 390, 160, "Dead-Letter Queue (DLQ)", "Catches Poisoned / Invalid Messages", "MaxReceiveCount = 3 Retries Exhausted", c_accent_red, "[ SQS DLQ ]")

    # Cards in Group 3 (Step Functions Tasks)
    draw_card(1150, 250, 520, 115, "Task 1: Validate Image", "Inspect File Signature & MIME Type", "Enforces Size Limits (<= 15MB, PNG/JPEG/WEBP)", c_accent_purple, "[ STEP FUNCTION TASK ]")
    draw_card(1150, 395, 520, 115, "Task 2: Extract Metadata", "Extract Dimensions, EXIF, Color Profile", "Calculates Aspect Ratio & MD5 Checksum", c_accent_purple, "[ STEP FUNCTION TASK ]")
    draw_card(1150, 540, 520, 115, "Task 3: Generate Thumbnail", "High-Quality Pillow Lanczos Resampling", "Produces 200x200 & 600x600 Scaled WebP", c_accent_purple, "[ STEP FUNCTION TASK ]")
    draw_card(1150, 685, 520, 115, "Task 4: Apply Watermark", "Alpha-Composite Dynamic Watermark", "Appends Branding & Timestamp Overlay", c_accent_purple, "[ STEP FUNCTION TASK ]")
    draw_card(1150, 830, 520, 115, "Task 5: Save & Catalog", "Uploads Output to Destination S3", "Persists Metadata to Amazon DynamoDB", c_accent_purple, "[ STEP FUNCTION TASK ]")
    draw_card(1150, 975, 520, 115, "Task 6: Publish Notification", "Dispatches Pipeline Event to SNS", "Includes Asset URLs, Dimensions & Timing", c_accent_purple, "[ STEP FUNCTION TASK ]")

    # Cards in Group 4
    draw_card(1790, 250, 510, 160, "Amazon S3 Destination", "Processed Asset Storage", "Lifecycle: S3 Standard -> Glacier (90d)", c_accent_green, "[ S3 DESTINATION ]")
    draw_card(1790, 450, 510, 160, "Amazon CloudFront CDN", "Global Edge Caching & Distribution", "Origin Access Control (OAC), HTTPS Enforced", c_accent_blue, "[ CLOUDFRONT ]")
    draw_card(1790, 650, 510, 160, "Amazon DynamoDB", "ImageMetadata Table (Pay-per-Request)", "PK: image_id, GSI: user_id + upload_time", c_accent_orange, "[ DYNAMODB ]")
    draw_card(1790, 850, 510, 160, "Amazon SNS Topic", "ImageProcessingTopic (Fan-out)", "Subscribers: Ops Email, SMS, Webhooks", c_accent_red, "[ AMAZON SNS ]")

    # Cards in Group 5 (Ops & Alarms)
    draw_card(90, 960, 420, 140, "Amazon CloudWatch Alarms", "Alarm: DLQ Message Depth > 0", "Alarm: Lambda Error Rate > 1%", c_accent_red, "[ CLOUDWATCH ]")
    draw_card(550, 960, 480, 140, "CloudWatch Logs & Metrics", "Structured JSON Logs across all Lambdas", "Step Functions Execution Visual Tracing", c_accent_orange, "[ LOGS & METRICS ]")

    # Flow Arrows & Badges
    # 1. Client -> API Gateway
    draw_arrow(draw, (320, 380), (320, 430), c_accent_blue, width=3)
    draw_step_badge(draw, (320, 405), 1, c_accent_blue, c_bg_dark, font_badge)

    # 2. API Gateway -> Lambda
    draw_arrow(draw, (320, 560), (320, 610), c_accent_blue, width=3)
    draw_step_badge(draw, (320, 585), 2, c_accent_blue, c_bg_dark, font_badge)

    # 3. Client direct PUT to S3 Source
    draw_arrow(draw, (90, 315), (55, 315), c_accent_green, width=3)
    draw_arrow(draw, (55, 315), (55, 805), c_accent_green, width=3)
    draw_arrow(draw, (55, 805), (90, 805), c_accent_green, width=3)
    draw_step_badge(draw, (55, 560), 3, c_accent_green, c_bg_dark, font_badge)

    # 4. S3 Source -> SQS Queue
    draw_arrow(draw, (550, 805), (610, 805), c_accent_orange, width=3)
    draw_arrow(draw, (610, 805), (610, 335), c_accent_orange, width=3)
    draw_arrow(draw, (610, 335), (650, 335), c_accent_orange, width=3)
    draw_step_badge(draw, (610, 570), 4, c_accent_orange, c_bg_dark, font_badge)

    # SQS to Consumer Lambda
    draw_arrow(draw, (845, 410), (845, 460), c_accent_orange, width=3)

    # SQS to DLQ on max retries
    draw_arrow(draw, (980, 410), (980, 660), c_accent_red, width=3)
    draw.text((910, 530), "Failures > 3", fill=c_accent_red, font=font_label)

    # 5. Consumer Lambda -> Step Functions Task 1
    draw_arrow(draw, (1040, 535), (1110, 535), c_accent_purple, width=3)
    draw_arrow(draw, (1110, 535), (1110, 305), c_accent_purple, width=3)
    draw_arrow(draw, (1110, 305), (1150, 305), c_accent_purple, width=3)
    draw_step_badge(draw, (1110, 420), 5, c_accent_purple, c_bg_dark, font_badge)

    # Step Functions Internal Transitions
    draw_arrow(draw, (1410, 365), (1410, 395), c_accent_purple, width=3)
    draw_arrow(draw, (1410, 510), (1410, 540), c_accent_purple, width=3)
    draw_arrow(draw, (1410, 655), (1410, 685), c_accent_purple, width=3)
    draw_arrow(draw, (1410, 800), (1410, 830), c_accent_purple, width=3)
    draw_arrow(draw, (1410, 945), (1410, 975), c_accent_purple, width=3)

    # 6. Step Function Save -> S3 Destination
    draw_arrow(draw, (1670, 860), (1730, 860), c_accent_green, width=3)
    draw_arrow(draw, (1730, 860), (1730, 330), c_accent_green, width=3)
    draw_arrow(draw, (1730, 330), (1790, 330), c_accent_green, width=3)
    draw_step_badge(draw, (1730, 595), 6, c_accent_green, c_bg_dark, font_badge)

    # 7. S3 Destination -> CloudFront CDN
    draw_arrow(draw, (2045, 410), (2045, 450), c_accent_blue, width=3)

    # 8. Step Function Save -> DynamoDB
    draw_arrow(draw, (1670, 890), (1750, 890), c_accent_orange, width=3)
    draw_arrow(draw, (1750, 890), (1750, 730), c_accent_orange, width=3)
    draw_arrow(draw, (1750, 730), (1790, 730), c_accent_orange, width=3)
    draw_step_badge(draw, (1750, 810), 7, c_accent_orange, c_bg_dark, font_badge)

    # 9. Step Function Notification -> SNS Topic
    draw_arrow(draw, (1670, 1030), (1770, 1030), c_accent_red, width=3)
    draw_arrow(draw, (1770, 1030), (1770, 930), c_accent_red, width=3)
    draw_arrow(draw, (1770, 930), (1790, 930), c_accent_red, width=3)
    draw_step_badge(draw, (1770, 980), 8, c_accent_red, c_bg_dark, font_badge)

    # DLQ -> CloudWatch Alarm -> Ops SNS
    draw_arrow(draw, (700, 820), (700, 880), c_accent_red, width=3)
    draw_arrow(draw, (700, 880), (300, 880), c_accent_red, width=3)
    draw_arrow(draw, (300, 880), (300, 960), c_accent_red, width=3)

    # Footer Notes
    footer_text = "Key Patterns: Direct Client S3 PUT via Presigned URLs  |  Asynchronous SQS Queue with DLQ  |  Step Functions Multi-Stage Orchestration  |  CloudFront CDN Edge Caching"
    draw.text((width // 2 - 620, height - 60), footer_text, fill=c_text_dim, font=font_footer)

    os.makedirs('architecture', exist_ok=True)
    img.save('architecture/solution-architecture.png', format='PNG')
    print("Successfully generated architecture/solution-architecture.png")

def generate_diagram_svg():
    svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 2400 1450" width="100%" height="100%">
  <defs>
    <style>
      .bg { fill: #0d1117; }
      .group-bg { fill: #161b22; opacity: 0.95; rx: 20px; }
      .card-bg { fill: #21262d; rx: 14px; }
      .title { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 44px; font-weight: bold; fill: #f0f6fc; }
      .subtitle { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 22px; font-weight: 600; fill: #ff9900; }
      .group-title { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 19px; font-weight: bold; }
      .card-title { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 20px; font-weight: bold; fill: #f0f6fc; }
      .card-sub1 { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 15px; font-weight: 600; }
      .card-sub2 { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 14px; fill: #8b949e; }
      .card-tag { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 13px; font-weight: bold; }
      .footer { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 16px; fill: #8b949e; text-anchor: middle; }
      .badge-text { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 17px; font-weight: bold; fill: #0d1117; text-anchor: middle; dominant-baseline: central; }
      .arrow { stroke-width: 3; fill: none; stroke-linecap: round; stroke-linejoin: round; }
    </style>
    <marker id="arrow-blue" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#58a6ff" />
    </marker>
    <marker id="arrow-orange" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#ff9900" />
    </marker>
    <marker id="arrow-green" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#3fb950" />
    </marker>
    <marker id="arrow-purple" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#bc8cff" />
    </marker>
    <marker id="arrow-red" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#f85149" />
    </marker>
  </defs>

  <rect width="100%" height="100%" class="bg" />

  <!-- Title -->
  <text x="1200" y="70" text-anchor="middle" class="title">Serverless Image Processing Pipeline</text>
  <text x="1200" y="115" text-anchor="middle" class="subtitle">AWS Solutions Architect (Associate) — Event-Driven Architecture with S3, SQS, Step Functions &amp; CloudFront</text>

  <!-- Group 1: Ingestion -->
  <rect x="60" y="180" width="520" height="680" class="group-bg" stroke="#58a6ff" stroke-width="2" stroke-dasharray="6,6" />
  <text x="85" y="218" class="group-title" fill="#58a6ff">1. INGESTION &amp; SECURE UPLOAD TIER</text>
  
  <!-- Cards in Ingestion -->
  <rect x="90" y="250" width="460" height="130" class="card-bg" stroke="#58a6ff" stroke-width="2" />
  <text x="110" y="275" class="card-tag" fill="#58a6ff">[ CLIENT ]</text>
  <text x="110" y="305" class="card-title">Web &amp; Mobile Clients</text>
  <text x="110" y="338" class="card-sub1" fill="#58a6ff">Frontend / API Consumers</text>
  <text x="110" y="362" class="card-sub2">Direct S3 Upload via Pre-signed URL</text>

  <rect x="90" y="430" width="460" height="130" class="card-bg" stroke="#58a6ff" stroke-width="2" />
  <text x="110" y="455" class="card-tag" fill="#58a6ff">[ API GATEWAY ]</text>
  <text x="110" y="485" class="card-title">Amazon API Gateway</text>
  <text x="110" y="518" class="card-sub1" fill="#58a6ff">REST API: GET /upload-url</text>
  <text x="110" y="542" class="card-sub2">Throttling, CORS, API Key Validation</text>

  <rect x="90" y="610" width="460" height="130" class="card-bg" stroke="#ff9900" stroke-width="2" />
  <text x="110" y="635" class="card-tag" fill="#ff9900">[ AWS LAMBDA ]</text>
  <text x="110" y="665" class="card-title">Presigned URL Lambda</text>
  <text x="110" y="698" class="card-sub1" fill="#ff9900">Python 3.12 Runtime</text>
  <text x="110" y="722" class="card-sub2">Generates Time-Limited S3 PUT URL</text>

  <rect x="90" y="770" width="460" height="70" class="card-bg" stroke="#3fb950" stroke-width="2" />
  <text x="110" y="795" class="card-tag" fill="#3fb950">[ S3 BUCKET ]</text>
  <text x="110" y="822" class="card-title">Amazon S3 Source (s3://raw-images)</text>

  <!-- Group 2: Queue Decoupling -->
  <rect x="620" y="180" width="450" height="680" class="group-bg" stroke="#ff9900" stroke-width="2" stroke-dasharray="6,6" />
  <text x="645" y="218" class="group-title" fill="#ff9900">2. ASYNCHRONOUS DECOUPLING (SQS)</text>

  <rect x="650" y="260" width="390" height="150" class="card-bg" stroke="#ff9900" stroke-width="2" />
  <text x="670" y="285" class="card-tag" fill="#ff9900">[ AMAZON SQS ]</text>
  <text x="670" y="315" class="card-title">Amazon SQS Queue</text>
  <text x="670" y="348" class="card-sub1" fill="#ff9900">Decouples Uploads from Pipeline</text>
  <text x="670" y="372" class="card-sub2">Batching, Retries (Visibility Timeout: 300s)</text>

  <rect x="650" y="460" width="390" height="150" class="card-bg" stroke="#ff9900" stroke-width="2" />
  <text x="670" y="485" class="card-tag" fill="#ff9900">[ AWS LAMBDA ]</text>
  <text x="670" y="515" class="card-title">Queue Consumer Lambda</text>
  <text x="670" y="548" class="card-sub1" fill="#ff9900">Event Source Mapping (Batch = 5)</text>
  <text x="670" y="572" class="card-sub2">Triggers Step Functions Execution</text>

  <rect x="650" y="660" width="390" height="160" class="card-bg" stroke="#f85149" stroke-width="2" />
  <text x="670" y="685" class="card-tag" fill="#f85149">[ SQS DLQ ]</text>
  <text x="670" y="715" class="card-title">Dead-Letter Queue (DLQ)</text>
  <text x="670" y="748" class="card-sub1" fill="#f85149">Catches Poisoned / Invalid Messages</text>
  <text x="670" y="772" class="card-sub2">MaxReceiveCount = 3 Retries Exhausted</text>

  <!-- Group 3: Step Functions -->
  <rect x="1110" y="180" width="600" height="960" class="group-bg" stroke="#bc8cff" stroke-width="2" stroke-dasharray="6,6" />
  <text x="1135" y="218" class="group-title" fill="#bc8cff">3. STEP FUNCTIONS WORKFLOW ORCHESTRATION</text>

  <rect x="1150" y="250" width="520" height="115" class="card-bg" stroke="#bc8cff" stroke-width="2" />
  <text x="1170" y="275" class="card-tag" fill="#bc8cff">[ STEP FUNCTION TASK ]</text>
  <text x="1170" y="305" class="card-title">Task 1: Validate Image</text>
  <text x="1170" y="335" class="card-sub2">Inspect File Signature &amp; MIME (&lt;= 15MB, PNG/JPEG/WEBP)</text>

  <rect x="1150" y="395" width="520" height="115" class="card-bg" stroke="#bc8cff" stroke-width="2" />
  <text x="1170" y="420" class="card-tag" fill="#bc8cff">[ STEP FUNCTION TASK ]</text>
  <text x="1170" y="450" class="card-title">Task 2: Extract Metadata</text>
  <text x="1170" y="480" class="card-sub2">Dimensions, EXIF, Aspect Ratio &amp; MD5 Checksum</text>

  <rect x="1150" y="540" width="520" height="115" class="card-bg" stroke="#bc8cff" stroke-width="2" />
  <text x="1170" y="565" class="card-tag" fill="#bc8cff">[ STEP FUNCTION TASK ]</text>
  <text x="1170" y="595" class="card-title">Task 3: Generate Thumbnail</text>
  <text x="1170" y="625" class="card-sub2">Pillow Lanczos Resampling (200x200 &amp; 600x600 WebP)</text>

  <rect x="1150" y="685" width="520" height="115" class="card-bg" stroke="#bc8cff" stroke-width="2" />
  <text x="1170" y="710" class="card-tag" fill="#bc8cff">[ STEP FUNCTION TASK ]</text>
  <text x="1170" y="740" class="card-title">Task 4: Apply Watermark</text>
  <text x="1170" y="770" class="card-sub2">Alpha-Composite Branding &amp; Timestamp Overlay</text>

  <rect x="1150" y="830" width="520" height="115" class="card-bg" stroke="#bc8cff" stroke-width="2" />
  <text x="1170" y="855" class="card-tag" fill="#bc8cff">[ STEP FUNCTION TASK ]</text>
  <text x="1170" y="885" class="card-title">Task 5: Save &amp; Catalog</text>
  <text x="1170" y="915" class="card-sub2">Uploads Output to S3 &amp; Persists Metadata in DynamoDB</text>

  <rect x="1150" y="975" width="520" height="115" class="card-bg" stroke="#bc8cff" stroke-width="2" />
  <text x="1170" y="1000" class="card-tag" fill="#bc8cff">[ STEP FUNCTION TASK ]</text>
  <text x="1170" y="1030" class="card-title">Task 6: Publish Notification</text>
  <text x="1170" y="1060" class="card-sub2">Dispatches Event to SNS with Asset URLs &amp; Metrics</text>

  <!-- Group 4: Persistence & Edge Delivery -->
  <rect x="1750" y="180" width="590" height="960" class="group-bg" stroke="#3fb950" stroke-width="2" stroke-dasharray="6,6" />
  <text x="1775" y="218" class="group-title" fill="#3fb950">4. PERSISTENCE &amp; GLOBAL DELIVERY</text>

  <rect x="1790" y="250" width="510" height="160" class="card-bg" stroke="#3fb950" stroke-width="2" />
  <text x="1810" y="275" class="card-tag" fill="#3fb950">[ S3 DESTINATION ]</text>
  <text x="1810" y="305" class="card-title">Amazon S3 Destination</text>
  <text x="1810" y="338" class="card-sub1" fill="#3fb950">Thumbnails &amp; Watermarked Assets</text>
  <text x="1810" y="362" class="card-sub2">Lifecycle: S3 Standard -&gt; Glacier (90 days)</text>

  <rect x="1790" y="450" width="510" height="160" class="card-bg" stroke="#58a6ff" stroke-width="2" />
  <text x="1810" y="475" class="card-tag" fill="#58a6ff">[ CLOUDFRONT CDN ]</text>
  <text x="1810" y="505" class="card-title">Amazon CloudFront</text>
  <text x="1810" y="538" class="card-sub1" fill="#58a6ff">Global Edge Caching &amp; Low Latency</text>
  <text x="1810" y="562" class="card-sub2">Origin Access Control (OAC), HTTPS Enforced</text>

  <rect x="1790" y="650" width="510" height="160" class="card-bg" stroke="#ff9900" stroke-width="2" />
  <text x="1810" y="675" class="card-tag" fill="#ff9900">[ AMAZON DYNAMODB ]</text>
  <text x="1810" y="705" class="card-title">Amazon DynamoDB</text>
  <text x="1810" y="738" class="card-sub1" fill="#ff9900">ImageMetadata Table (Pay-per-Request)</text>
  <text x="1810" y="762" class="card-sub2">PK: image_id | GSI: user_id + upload_time</text>

  <rect x="1790" y="850" width="510" height="160" class="card-bg" stroke="#f85149" stroke-width="2" />
  <text x="1810" y="875" class="card-tag" fill="#f85149">[ AMAZON SNS ]</text>
  <text x="1810" y="905" class="card-title">Amazon SNS Topic</text>
  <text x="1810" y="938" class="card-sub1" fill="#f85149">ImageProcessingTopic (Fan-out)</text>
  <text x="1810" y="962" class="card-sub2">Subscribers: Ops Email, SMS, Webhooks</text>

  <!-- Group 5: Observability -->
  <rect x="60" y="900" width="1010" height="240" class="group-bg" stroke="#f85149" stroke-width="2" stroke-dasharray="6,6" />
  <text x="85" y="938" class="group-title" fill="#f85149">5. OBSERVABILITY, RESILIENCE &amp; DEAD-LETTER RECOVERY</text>

  <rect x="90" y="960" width="420" height="140" class="card-bg" stroke="#f85149" stroke-width="2" />
  <text x="110" y="985" class="card-tag" fill="#f85149">[ CLOUDWATCH ALARMS ]</text>
  <text x="110" y="1015" class="card-title">Amazon CloudWatch</text>
  <text x="110" y="1048" class="card-sub1" fill="#f85149">DLQ Message Depth &gt; 0 Alert</text>
  <text x="110" y="1072" class="card-sub2">Lambda Error Rate &gt; 1% Alert</text>

  <rect x="550" y="960" width="480" height="140" class="card-bg" stroke="#ff9900" stroke-width="2" />
  <text x="570" y="985" class="card-tag" fill="#ff9900">[ LOGS &amp; METRICS ]</text>
  <text x="570" y="1015" class="card-title">CloudWatch Logs &amp; Metrics</text>
  <text x="570" y="1048" class="card-sub1" fill="#ff9900">Structured JSON Logs across all Lambdas</text>
  <text x="570" y="1072" class="card-sub2">Step Functions Execution Visual Tracing</text>

  <!-- Arrows -->
  <!-- 1. Client to API GW -->
  <path d="M 320 380 L 320 422" class="arrow" stroke="#58a6ff" marker-end="url(#arrow-blue)" />
  <circle cx="320" cy="405" r="16" fill="#58a6ff" />
  <text x="320" y="405" class="badge-text">1</text>

  <!-- 2. API GW to Lambda -->
  <path d="M 320 560 L 320 602" class="arrow" stroke="#58a6ff" marker-end="url(#arrow-blue)" />
  <circle cx="320" cy="585" r="16" fill="#58a6ff" />
  <text x="320" y="585" class="badge-text">2</text>

  <!-- 3. Direct S3 Upload -->
  <path d="M 90 315 L 55 315 L 55 805 L 82 805" class="arrow" stroke="#3fb950" marker-end="url(#arrow-green)" />
  <circle cx="55" cy="560" r="16" fill="#3fb950" />
  <text x="55" y="560" class="badge-text">3</text>

  <!-- 4. S3 Source to SQS -->
  <path d="M 550 805 L 610 805 L 610 335 L 642 335" class="arrow" stroke="#ff9900" marker-end="url(#arrow-orange)" />
  <circle cx="610" cy="570" r="16" fill="#ff9900" />
  <text x="610" y="570" class="badge-text">4</text>

  <!-- SQS to Consumer -->
  <path d="M 845 410 L 845 452" class="arrow" stroke="#ff9900" marker-end="url(#arrow-orange)" />

  <!-- SQS to DLQ -->
  <path d="M 980 410 L 980 652" class="arrow" stroke="#f85149" marker-end="url(#arrow-red)" />
  <text x="910" y="535" font-family="sans-serif" font-size="14px" font-weight="bold" fill="#f85149">Failures &gt; 3</text>

  <!-- 5. Consumer Lambda to Step Functions -->
  <path d="M 1040 535 L 1110 535 L 1110 305 L 1142 305" class="arrow" stroke="#bc8cff" marker-end="url(#arrow-purple)" />
  <circle cx="1110" cy="420" r="16" fill="#bc8cff" />
  <text x="1110" y="420" class="badge-text">5</text>

  <!-- Step Functions transitions -->
  <path d="M 1410 365 L 1410 387" class="arrow" stroke="#bc8cff" marker-end="url(#arrow-purple)" />
  <path d="M 1410 510 L 1410 532" class="arrow" stroke="#bc8cff" marker-end="url(#arrow-purple)" />
  <path d="M 1410 655 L 1410 677" class="arrow" stroke="#bc8cff" marker-end="url(#arrow-purple)" />
  <path d="M 1410 800 L 1410 822" class="arrow" stroke="#bc8cff" marker-end="url(#arrow-purple)" />
  <path d="M 1410 945 L 1410 967" class="arrow" stroke="#bc8cff" marker-end="url(#arrow-purple)" />

  <!-- 6. Step Function to Destination S3 -->
  <path d="M 1670 860 L 1730 860 L 1730 330 L 1782 330" class="arrow" stroke="#3fb950" marker-end="url(#arrow-green)" />
  <circle cx="1730" cy="595" r="16" fill="#3fb950" />
  <text x="1730" y="595" class="badge-text">6</text>

  <!-- 7. S3 Destination to CloudFront -->
  <path d="M 2045 410 L 2045 442" class="arrow" stroke="#58a6ff" marker-end="url(#arrow-blue)" />

  <!-- 8. Step Function to DynamoDB -->
  <path d="M 1670 890 L 1750 890 L 1750 730 L 1782 730" class="arrow" stroke="#ff9900" marker-end="url(#arrow-orange)" />
  <circle cx="1750" cy="810" r="16" fill="#ff9900" />
  <text x="1750" y="810" class="badge-text">7</text>

  <!-- 9. Step Function to SNS -->
  <path d="M 1670 1030 L 1770 1030 L 1770 930 L 1782 930" class="arrow" stroke="#f85149" marker-end="url(#arrow-red)" />
  <circle cx="1770" cy="980" r="16" fill="#f85149" />
  <text x="1770" y="980" class="badge-text">8</text>

  <!-- DLQ to CloudWatch Alarm -->
  <path d="M 700 820 L 700 880 L 300 880 L 300 952" class="arrow" stroke="#f85149" marker-end="url(#arrow-red)" />

  <!-- Footer -->
  <text x="1200" y="1410" class="footer">Key Patterns: Direct Client S3 PUT via Presigned URLs  |  Asynchronous SQS Queue with DLQ  |  Step Functions Multi-Stage Orchestration  |  CloudFront CDN Edge Caching</text>
</svg>"""
    with open('architecture/solution-architecture.svg', 'w', encoding='utf-8') as f:
        f.write(svg_content)
    print("Successfully generated architecture/solution-architecture.svg")

def generate_drawio_xml():
    drawio_content = """<mxfile host="Electron" modified="2026-09-27T08:00:00.000Z" agent="Antigravity" version="21.6.8" type="device">
  <diagram id="serverless-image-pipeline" name="Solution Architecture">
    <mxGraphModel dx="1422" dy="845" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1600" pageHeight="1000" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        
        <mxCell id="grp_ingest" value="1. INGESTION &amp; UPLOAD TIER" style="rounded=1;whiteSpace=wrap;html=1;verticalAlign=top;dashed=1;dashPattern=5 5;fillColor=#161b22;strokeColor=#58a6ff;fontColor=#58a6ff;fontStyle=1;fontSize=14;opacity=90;" vertex="1" parent="1">
          <mxGeometry x="60" y="80" width="340" height="480" as="geometry" />
        </mxCell>
        
        <mxCell id="grp_queue" value="2. DECOUPLING TIER" style="rounded=1;whiteSpace=wrap;html=1;verticalAlign=top;dashed=1;dashPattern=5 5;fillColor=#161b22;strokeColor=#ff9900;fontColor=#ff9900;fontStyle=1;fontSize=14;opacity=90;" vertex="1" parent="1">
          <mxGeometry x="440" y="80" width="280" height="480" as="geometry" />
        </mxCell>

        <mxCell id="grp_sfn" value="3. STEP FUNCTIONS ORCHESTRATION" style="rounded=1;whiteSpace=wrap;html=1;verticalAlign=top;dashed=1;dashPattern=5 5;fillColor=#161b22;strokeColor=#bc8cff;fontColor=#bc8cff;fontStyle=1;fontSize=14;opacity=90;" vertex="1" parent="1">
          <mxGeometry x="760" y="80" width="360" height="740" as="geometry" />
        </mxCell>

        <mxCell id="grp_dest" value="4. PERSISTENCE &amp; DELIVERY" style="rounded=1;whiteSpace=wrap;html=1;verticalAlign=top;dashed=1;dashPattern=5 5;fillColor=#161b22;strokeColor=#3fb950;fontColor=#3fb950;fontStyle=1;fontSize=14;opacity=90;" vertex="1" parent="1">
          <mxGeometry x="1160" y="80" width="340" height="740" as="geometry" />
        </mxCell>

        <mxCell id="grp_ops" value="5. OBSERVABILITY &amp; DLQ ALERTS" style="rounded=1;whiteSpace=wrap;html=1;verticalAlign=top;dashed=1;dashPattern=5 5;fillColor=#161b22;strokeColor=#f85149;fontColor=#f85149;fontStyle=1;fontSize=14;opacity=90;" vertex="1" parent="1">
          <mxGeometry x="60" y="600" width="660" height="220" as="geometry" />
        </mxCell>

        <mxCell id="node_client" value="Web / Mobile Client&#xa;(Direct Upload)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#21262d;strokeColor=#58a6ff;fontColor=#ffffff;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="90" y="140" width="130" height="70" as="geometry" />
        </mxCell>

        <mxCell id="node_apigw" value="Amazon API Gateway&#xa;GET /upload-url" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#21262d;strokeColor=#58a6ff;fontColor=#ffffff;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="250" y="140" width="130" height="70" as="geometry" />
        </mxCell>

        <mxCell id="node_lambda_url" value="AWS Lambda&#xa;Presigned URL Signer" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#21262d;strokeColor=#ff9900;fontColor=#ffffff;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="250" y="270" width="130" height="70" as="geometry" />
        </mxCell>

        <mxCell id="node_s3_raw" value="S3 Source Bucket&#xa;(Raw Images)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#21262d;strokeColor=#3fb950;fontColor=#ffffff;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="90" y="270" width="130" height="70" as="geometry" />
        </mxCell>

        <mxCell id="node_sqs" value="Amazon SQS&#xa;Image Processing Queue" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#21262d;strokeColor=#ff9900;fontColor=#ffffff;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="480" y="140" width="200" height="70" as="geometry" />
        </mxCell>

        <mxCell id="node_dlq" value="Amazon SQS DLQ&#xa;Dead Letter Queue" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#21262d;strokeColor=#f85149;fontColor=#ffffff;" vertex="1" parent="1">
          <mxGeometry x="480" y="270" width="200" height="70" as="geometry" />
        </mxCell>

        <mxCell id="sfn_val" value="1. Validate Image&#xa;(MIME &amp; Size)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#21262d;strokeColor=#bc8cff;fontColor=#ffffff;" vertex="1" parent="1">
          <mxGeometry x="800" y="150" width="280" height="60" as="geometry" />
        </mxCell>
        <mxCell id="sfn_meta" value="2. Extract Metadata&#xa;(Dimensions &amp; EXIF)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#21262d;strokeColor=#bc8cff;fontColor=#ffffff;" vertex="1" parent="1">
          <mxGeometry x="800" y="260" width="280" height="60" as="geometry" />
        </mxCell>
        <mxCell id="sfn_thumb" value="3. Generate Thumbnail&#xa;(Pillow 200x200)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#21262d;strokeColor=#bc8cff;fontColor=#ffffff;" vertex="1" parent="1">
          <mxGeometry x="800" y="370" width="280" height="60" as="geometry" />
        </mxCell>
        <mxCell id="sfn_wm" value="4. Apply Watermark&#xa;(Overlay &amp; Opacity)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#21262d;strokeColor=#bc8cff;fontColor=#ffffff;" vertex="1" parent="1">
          <mxGeometry x="800" y="480" width="280" height="60" as="geometry" />
        </mxCell>
        <mxCell id="sfn_store" value="5. Persist &amp; Notify&#xa;(S3 + DynamoDB + SNS)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#21262d;strokeColor=#bc8cff;fontColor=#ffffff;" vertex="1" parent="1">
          <mxGeometry x="800" y="590" width="280" height="60" as="geometry" />
        </mxCell>

        <mxCell id="node_s3_dest" value="S3 Destination Bucket&#xa;(Thumbnails &amp; Watermarked)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#21262d;strokeColor=#3fb950;fontColor=#ffffff;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="1210" y="150" width="240" height="80" as="geometry" />
        </mxCell>

        <mxCell id="node_cf" value="Amazon CloudFront&#xa;Global CDN Distribution" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#21262d;strokeColor=#58a6ff;fontColor=#ffffff;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="1210" y="310" width="240" height="80" as="geometry" />
        </mxCell>

        <mxCell id="node_ddb" value="Amazon DynamoDB&#xa;ImageMetadata Table" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#21262d;strokeColor=#ff9900;fontColor=#ffffff;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="1210" y="470" width="240" height="80" as="geometry" />
        </mxCell>

        <mxCell id="node_cw" value="CloudWatch Alarms&#xa;(DLQ Depth &amp; Lambda Errors)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#21262d;strokeColor=#f85149;fontColor=#ffffff;" vertex="1" parent="1">
          <mxGeometry x="100" y="660" width="220" height="70" as="geometry" />
        </mxCell>
        <mxCell id="node_sns" value="Amazon SNS Topic&#xa;(Operator Email Alerts)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#21262d;strokeColor=#f85149;fontColor=#ffffff;" vertex="1" parent="1">
          <mxGeometry x="380" y="660" width="220" height="70" as="geometry" />
        </mxCell>

        <mxCell id="e1" value="1. Request URL" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#58a6ff;fontColor=#58a6ff;" edge="1" parent="1" source="node_client" target="node_apigw">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="e2" value="2. Generate Token" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#58a6ff;fontColor=#58a6ff;" edge="1" parent="1" source="node_apigw" target="node_lambda_url">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="e3" value="3. PUT S3 Direct" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#3fb950;fontColor=#3fb950;" edge="1" parent="1" source="node_client" target="node_s3_raw">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="e4" value="4. s3:ObjectCreated" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#ff9900;fontColor=#ff9900;" edge="1" parent="1" source="node_s3_raw" target="node_sqs">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="e5" value="5. Start Execution" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#bc8cff;fontColor=#bc8cff;" edge="1" parent="1" source="node_sqs" target="sfn_val">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="e_sfn1" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#bc8cff;" edge="1" parent="1" source="sfn_val" target="sfn_meta">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="e_sfn2" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#bc8cff;" edge="1" parent="1" source="sfn_meta" target="sfn_thumb">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="e_sfn3" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#bc8cff;" edge="1" parent="1" source="sfn_thumb" target="sfn_wm">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="e_sfn4" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#bc8cff;" edge="1" parent="1" source="sfn_wm" target="sfn_store">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="e6" value="6. Store Images" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#3fb950;fontColor=#3fb950;" edge="1" parent="1" source="sfn_store" target="node_s3_dest">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="e7" value="7. Save Record" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#ff9900;fontColor=#ff9900;" edge="1" parent="1" source="sfn_store" target="node_ddb">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="e8" value="8. Edge Cache" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#58a6ff;fontColor=#58a6ff;" edge="1" parent="1" source="node_s3_dest" target="node_cf">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="e9" value="Failures &gt; 3 retries" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#f85149;fontColor=#f85149;" edge="1" parent="1" source="node_sqs" target="node_dlq">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="e10" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#f85149;" edge="1" parent="1" source="node_dlq" target="node_cw">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="e11" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#f85149;" edge="1" parent="1" source="node_cw" target="node_sns">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>"""
    out_drawio = 'architecture/solution-architecture.drawio'
    with open(out_drawio, 'w', encoding='utf-8') as f:
        f.write(drawio_content)
    print(f"Successfully generated {out_drawio}")

if __name__ == '__main__':
    generate_diagram_png()
    generate_diagram_svg()
    generate_drawio_xml()

