# 学習再開メモ

`docker-compose stop` で止めた状態からの再開手順。詳しい構成図は [ARCHITECTURE.html](ARCHITECTURE.html)、MinIOの詰まりポイントは [MINIO-NOTES.md](MINIO-NOTES.md) を参照。

## 再開（データはそのまま残っている前提）

```fish
cd wdpressplus-bigdata
docker-compose start
```

`docker-compose up -d` でも同じ。`./data`（MinIO）や metastore-db / datamart の中身は
`stop` では消えないので、`/initSchema` やバケット作成のやり直しは不要。

確認:

```fish
docker-compose ps
```

全サービスが `Up` になっていればOK。

- MinIO: http://localhost:9000
- Metabase: http://localhost:13000

## presto-cli を叩く

```fish
docker-compose run --rm presto-cli
```

```sql
SHOW TABLES;
SELECT * FROM uscrn LIMIT 5;
```

## 学習を終えて止めるとき（再開する前提）

```fish
docker-compose stop
```

コンテナは残るが停止するのでリソースを食わない。データも消えない。

## 完全に片付けたいとき（最初からやり直す前提）

```fish
docker-compose down
```

⚠️ metastore-db と datamart は名前付きボリュームがないため、コンテナと一緒に
**中身（テーブル定義・集計結果）も消える**。MinIO の `./data` はホストマウントなので消えない。
`down` した場合は README の手順（`/initSchema` から）をやり直す。

## ゼロから作り直したいとき（MinIOのデータも含めて）

```fish
docker-compose down
rm -rf data
docker-compose up -d minio
# バケット作り直し（MINIO-NOTES.md 参照）
```

## つまずいたら

- MinIOの接続・バケット関連 → [MINIO-NOTES.md](MINIO-NOTES.md)
- コンテナ同士の関係（MinIO / Metastore / PostgreSQL の役割分担）→ [ARCHITECTURE.html](ARCHITECTURE.html)
- Metastoreが実際に使われているか実感したい → ARCHITECTURE.html の「もう一段深く」的な実験
  （`docker-compose stop metastore` してから SELECT を叩くとエラーになる、など）
