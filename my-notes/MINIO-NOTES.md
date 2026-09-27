# MinIO のつまづきポイント（macOS / fish）

検証環境: macOS (Darwin 25.3.0) / arm64 / fish / MinIO RELEASE.2025-09-07
記録日: 2026-08-30

前提: Docker Desktop と awscli (`uv tool install awscli`) は導入済み。

---

## 0. 結論（これだけやれば動く）

```fish
# 起動
docker compose up -d minio

# MinIO 用プロファイルを作る
aws configure set --profile minio aws_access_key_id accesskey
aws configure set --profile minio aws_secret_access_key secretkey
aws configure set --profile minio region us-east-1
aws configure set --profile minio endpoint_url http://localhost:9000

# バケット作成
for name in datalake warehouse prefect
    aws --profile minio s3api create-bucket --bucket $name
end

# 確認
aws --profile minio s3 ls
```

---

## 1. `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` は非推奨

起動ログに出る。

```
INFO: WARNING: MINIO_ACCESS_KEY and MINIO_SECRET_KEY are deprecated.
         Please use MINIO_ROOT_USER and MINIO_ROOT_PASSWORD
```

現行 MinIO では警告のみで**まだ動く**。将来削除される可能性あり。
書籍の記述と揃えるため `docker-compose.yml` はそのままにしてある。
認証が通らなくなったら以下に置換する。

```yaml
    environment:
      - MINIO_ROOT_USER=accesskey
      - MINIO_ROOT_PASSWORD=secretkey
```

なお `MINIO_ROOT_PASSWORD` は8文字以上が必要。`secretkey` は9文字なのでそのまま通る。

## 2. 管理画面がブラウザで開けない

現行 MinIO は WebUI が**ランダムポート**で起動し、ホストに公開されていない。

```
API:   http://127.0.0.1:9000
WebUI: http://127.0.0.1:36693     ← 毎回変わる／ホストからは見えない
```

見たい場合は `docker-compose.yml` の minio に以下を追加する。

```yaml
    command: server /data --console-address :9001
    ports:
      - 9000:9000
      - 9001:9001
```

CLI (`aws s3`) だけで進めるなら不要。

## 3. `Unable to locate credentials`

`aws configure set --profile minio ...` で設定したなら、**実行側にも `--profile minio` が要る**。
付け忘れると `default` プロファイルを見にいって落ちる。

```fish
# ✗ 設定したのに落ちる
aws --endpoint-url http://localhost:9000 s3api create-bucket --bucket datalake

# ✓
aws --profile minio s3api create-bucket --bucket datalake
```

毎回付けたくなければセッション既定にする。

```fish
set -x AWS_PROFILE minio     # このセッションのみ
set -Ux AWS_PROFILE minio    # fish全体に永続（本物のAWSも使うなら非推奨）
```

プロファイルに `endpoint_url` を入れておくと `--endpoint-url http://localhost:9000` を
毎回打たずに済む（botocore 1.31以降の機能）。入れない場合は毎回付ける。

## 4. バケット名のタイプミスは静かに通る

`datalekd` のような打ち間違いでもバケットは作成され、エラーにならない。
Spark から読み出す段になって初めて気づくので注意。

**必要なバケット**

| バケット | 用途 | 参照 |
| --- | --- | --- |
| `datalake` | 生データ置き場（USCRN） | `flows/download.py`, `scripts/warehouse.py` |
| `warehouse` | Hive ウェアハウス領域 | `containers/hive-metastore/conf/metastore-site.xml` |
| `prefect` | Prefect のフロー保存用（後の章） | — |

`s3api create-bucket` は成功すると `{"Location": "/datalake"}` を返す。
無言で済ませたいなら `aws --profile minio s3 mb s3://datalake` でもよい。

## 5. fish の for ループは `do` / `done` ではない

書籍やWebの bash 例をそのまま貼ると、fish は `end` を待って**無反応になる**
（フリーズではなく入力待ち）。`Ctrl+C` で抜ける。

```fish
# ✗ bash
for name in a b c; do cmd $name; done

# ✓ fish
for name in a b c
    cmd $name
end

# ✓ fish 1行版
for name in a b c; cmd $name; end
```

環境変数も `export X=y` ではなく `set -x X y`。

---

## データの実体

`./data:/data` をマウントしているので、バケットはホストの `./data/` 配下に見える。

```
data/
├── .minio.sys/     ← MinIO の内部メタデータ
├── datalake/
├── warehouse/
└── prefect/
```

作り直したいときは MinIO を止めて `./data` を消す。

```fish
docker compose stop minio
rm -rf data
docker compose up -d minio
```
