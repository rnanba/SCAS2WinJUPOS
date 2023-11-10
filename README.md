# SCAS2WinJUPOS

## 概要

SharpCap 4 で撮影した動画を AutoStakkert! 3 でスタックした画像ファイルに対して WinJUPOS での処理に適したファイル名のコピーもしくはハードリンクを生成します。

生成された画像ファイル名のタイムスタンプ部分にはキャプチャー時間の中央時刻が入り、WinJUPOS の Image Measurement で画像ファイル読み込むと撮影時刻が自動入力されます。AutoStakkert! 3 で Limit Frames を設定した場合も対象フレームのキャプチャ時間の中央時刻の推定値を計算してファイル名に設定します。

## 動作環境

- Python 3.8 以降

以下、コマンドライン操作についての記述は Linux 環境を例にしています。Windows, macOS 等、他の環境での操作については適宣読み替えてください。コマンドラインで `SCAS2WinJUPOS.py` で Python スクリプトが実行できない環境では `python SCAS2WinJUPOS.py` のようにすると実行できるかもしれません。

## 使用法
```
SCAS2WinJUPOS.py [-p pattern] [-l] [-o observer] [-i imageinfo] [--dry-run] sc_dir as_dir target_dir
```

### 引数

| 引数      | 説明 |
|---|---|
| `sc_dir` | SharpCap 4 のキャプチャの保存先ディレクトリです。SharpCap 4 の撮影データファイル(ファイル名書式 *HH_MM_SS*.CameraSettins.txt のファイル)が保存されているものとします。|
| `as_dir` | AutoStakkert! 3 のスタック結果の保存先ディレクトリです。ファイル名が HH_MM_SS 書式のタイムスタンプで始まるスタック済画像ファイル(もしくはそれを後処理したもの)が保存されているものとします。タイムスタンプで始まり、かつ　`-o pattern` オプションで指定したパターンにマッチするファイルがこのスクリプトの処理対象の画像ファイルになります。|
| `target_dir` | スクリプトが生成した画像ファイルのコピーまたはハードリンク(`-l` オプションを指定した場合)の保存先ディレクトリです。ディレクトリが存在しなければ自動的に生成されます。<br>このディレクトリに 画像ファイルのコピーまたはハードリンクが *YYYY-MM-DD.T-OBSERVER[-IMAGEINFO]* の書式(WinJUPOS-Conventions 形式) のファイル名で保存されます。タイムスタンプ部分の日時はキャプチャー時間の中央時刻です。中央時刻は、通常 SharpCap 4 が保存した撮影データファイルの MidCapture 値から生成します。スタック済み画像ファイルのファイル名に limit*{開始フレーム}*-*{終了フレーム}* の書式のフィールドがある場合は(AutoStakkert!3 で Limit Frames を設定した場合)中間フレームのキャプチャ時刻を平均フレームレートから推定して中央時刻とします。<br>WinJUPOS-Conventions 形式のファイル名の画像ファイルを WinJUPOS の Image measurement で読み込むと撮影時刻が自動的に入力されます。|

### オプション

| オプション     | 説明 |
|---|---|
| `-p pattern` | スタック済画像ファイル(もしくはそれを後処理したもの)のファイル名のパターンとして *pattern* を指定します。パターンはワイルドカード形式で記述します。UNIX 系のシェルのコマンドラインから指定する場合はパターンを `''` で括って指定してください。省略時は `-p '*.tif'` になります。|
| `-l` | スクリプトが生成する画像ファイルを元の画像のコピーではなくハードリンクにすることを指定します。通常ハードリンクは同じファイルシステム(Windows なら同じドライブ等)内でした生成できません。|
| `-o observer` | 観測者の名前として *observer* を指定します。*observer* にはハイフン(-)を含まない半角英数文字からなる文字列を指定します。ここで指定した値がスクリプトが生成する WinJUPOS-Conventions 形式のファイル名の *OBSERVER* の値として使用されます。省略時は環境変数 `USERNAME` または `USER` の値になります。|
| `-i imageinfo` | オプションの画像情報として *imageinfo* を指定します。*imageinfo* にはハイフン(-)を含まない半角英数文字からなる文字列を指定します。ここで指定した値がスクリプトが生成する WinJUPOS-Conventions 形式のファイル名の *IMAGEINFO* の値として使用されます。省略時は空値になります。<br>imageinfo 文字列中に *{変数名}* の形で変数を指定すると変数の展開後の文字列が *IMAGEINFO* の値になります(指定可能な変数については後述)。|
| `--dry-run` | ディレクトリやファイルの作成を行わずに実行します。生成される画像ファイルのファイル名を事前に確認する際に使用します。|
| `--version` | このスクリプトのバージョンを表示して終了します。|
| `--help` | このスクリプトのヘルプメッセージを表示して終了します。|

### imageinfo に指定可能な変数

`-i imageinfo` オプションの *imageinfo* に指定可能な変数は以下の通りです。

| 変数名 | 説明 |
|--------|------|
| `cam`  | カメラ名です。値として SharpCap 4 が保存した *.CameraSettins.txt の先頭行のセクション名が使用されます。名前に含まれる空白は除去されます(例: ZWO ASI290MM → ZWOASI290MM)。|
| `ff`   | AutoStakkert! 3 のファイル名に含まれる Free Field 値です。値に含まれる空白とハイフンは除去されます。<br>AutoStakkert! 3 のファイル名パターン設定の先頭部分が `[bn][ff]` になっているものと仮定します(それがデフォルト設定です)。ただし、パターンに曖昧さがあるため Free Field が指定されていない場合はその次のフィールド値が使用されるという制限があります。|

## 使用例

以下のディレクトツリーとファイル構成で、ログインユーザー名 `nanba` のユーザーがディレクトリ `/2023-11-01` に cd して実行するものとします。

```
/
  2023-11-01/
    19_44_51.CameraSettings.txt
      # SharpCap 4 の撮影データファイル。
      # 先頭行は [ZWO ASI290MM]
      # MidCapture=2023-11-01T10:45:16.7735392Z
    22_28_08.CameraSettings.txt
      # SharpCap 4 の撮影データファイル。
      # 先頭行は [ZWO ASI290MM]
      # StartCapture=2023-11-01T13:28:08.5058266Z
      # MidCapture=2023-11-01T13:28:35.6078266Z
      # EndCapture=2023-11-01T13:29:02.7100920Z
      # FrameCount=3000
    
    AS_F1500/
      19_44_51_M180C_l4_ap249.tif
        # AutoStakkert! 3 で Free Field に "M180C" を指定してスタック
        # した画像ファイル。
      19_44_51_M180C_l4_ap249-wavelet.png
        # 19_44_51_M180C_l4_ap249.tif を wavelet 処理した画像ファイル。
    
    AS_F500/
      22_28_08_limit000000-001000_lapl7_ap234.tif
        # AutoStakkert! 3 で Limit Frames の Min frame # に 0,
        # Max frame # に 1000 を指定してスタックした画像ファイル。
```

例1: 
```
SCAS2WinJUPOS.py . AS_F1500 WinJUPOS
```
カレントディレクトリから `19_44_51.CameraSettings.txt` を、ディレクトリ `AS_F1500` から `19_44_51_M180C_l4_ap249.tif` を読み込み、ディレクトリ `WinJUPOS` にコピーします。コピーされた画像ファイルのファイル名は `2023-11-01-1045.3-nanba.tif` になります。

例2:
```
SCAS2WinJUPOS.py -p '*-wavelet.png' . AS_F1500 WinJUPOS
```
カレントディレクトリから `19_44_51.CameraSettings.txt` を、ディレクトリ `AS_F1500 から 19_44_51_M180C_l4_ap249-wavelet.png` を読み込み、ディレクトリ `WinJUPOS` にコピーします。コピーされた画像ファイルのファイル名は `2023-11-01-1045.3-nanba.png` になります。

例3:
```
SCAS2WinJUPOS.py -o RN -i '{cam}' . AS_F1500 WinJUPOS
```
カレントディレクトリから `19_44_51.CameraSettings.txt` を、ディレクトリ `AS_F1500 から 19_44_51_M180C_l4_ap249.tif` を読み込み、ディレクトリ `WinJUPOS` にコピーします。コピーされた画像ファイルのファイル名は `2023-11-01-1045.3-RN-ZWOASI290MM.tif` になります。

例4:
```
SCAS2WinJUPOS.py -o RN -i '{cam}' . AS_F500 WinJUPOS
```
カレントディレクトリから `22_28_08.CameraSettings.txt` を、ディレクトリ `AS_F500` から `22_28_08_limit000000-001000_lapl7_ap234.tif` を読み込み、ディレクトリ `WinJUPOS` にコピーします。コピーされた画像ファイルのファイル名は `2023-11-01-1328.3-RN-ZWOASI290MM.tif` になります。

## ライセンス

MITライセンスです。
