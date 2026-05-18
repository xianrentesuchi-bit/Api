import os
import requests
import yt_dlp
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse

app = FastAPI(title="Xvideos Stream Linker")


def get_working_proxy():
    """無料のプロキシリストから、今動いているものを1つ取得する"""
    try:
        # 無料プロキシのAPIからリストを取得
        response = requests.get(
            "https://pubproxy.com/api/proxy?limit=1&format=txt&http=true&country=US,JP,DE"
        )
        if response.status_code == 200 and response.text.strip():
            proxy = f"http://{response.text.strip()}"
            return proxy
    except Exception:
        pass
    # 取得に失敗した場合は、Renderの生IPで試すためにNoneを返す
    return None


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
    # 動いているプロキシをその場で取得
    dynamic_proxy = get_working_proxy()

    # yt-dlpのオプション設定
    ydl_opts = {
        "simulate": True,  # 動画本体はダウンロードしない
        "quiet": True,  # ログ出力を抑制
        "format": "best",  # 最高画質を選択
        "no_warnings": True,
    }

    # プロキシが見つかった場合のみ設定に追加
    if dynamic_proxy:
        ydl_opts["proxy"] = dynamic_proxy

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
                "used_proxy": dynamic_proxy
                or "None (Direct)",  # どのプロキシを使ったかデバッグ用
            }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"yt-dlpでの解析に失敗しました。使用プロキシ: {dynamic_proxy} エラー: {str(e)}",
        )
