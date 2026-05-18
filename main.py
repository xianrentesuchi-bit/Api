import os
import yt_dlp
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse

app = FastAPI(title="Xvideos Stream Linker")

# 提供されたプロキシ
PROXY_URL = "http://ytproxy-siawaseok.duckdns.org:3007"


@app.get("/", response_class=HTMLResponse)
def index():
    """ブラウザでアクセスしたときに見える簡易確認画面"""
    return """
    <html>
        <head><title>Stream Extractor</title></head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 40px auto; padding: 20px;">
            <h2>Xvideos ストリーム取得API</h2>
            <p>以下のURL形式でストリームURLを取得できます：</p>
            <code>/get_stream?url=【動画のURL】</code>
            <br><br>
            <form action="/get_stream" method="get">
                <input type="text" name="url" placeholder="https://www.xvideos.com/video..." style="width: 80%; padding: 8px;">
                <button type="submit" style="padding: 8px 15px;">取得</button>
            </form>
        </body>
    </html>
    """


@app.get("/get_stream")
def get_stream(url: str = Query(..., description="Xvideosの動画URL")):
    # yt-dlpのオプション設定
    ydl_opts = {
        "simulate": True,  # 動画本体はダウンロードしない
        "quiet": True,  # ログ出力を抑制
        "format": "best",  # 最高画質を選択
        "proxy": PROXY_URL,  # 指定されたプロキシを使用
        "no_warnings": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 動画情報の抽出
            info = ydl.extract_info(url, download=False)

            # ストリームURL（通常は.m3u8、環境によっては.mp4）を取得
            stream_url = info.get("url")

            if not stream_url:
                raise HTTPException(
                    status_code=404,
                    detail="ストリームURLが見つかりませんでした。",
                )

            return {
                "status": "success",
                "title": info.get("title"),
                "duration": info.get("duration"),
                "stream_url": stream_url,
            }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"yt-dlpでの解析に失敗しました。プロキシが落ちているか、URLが不正な可能性があります。エラー: {str(e)}",
        )
