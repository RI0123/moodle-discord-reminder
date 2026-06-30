# Moodle課題リマインダー (Discord通知)

MoodleのカレンダーエクスポートURLから課題の締切を取得し、締切が近づいたらDiscordに自動通知するBotです。
GitHub Actionsで毎日自動実行されるので、サーバーを用意する必要はありません。

## セットアップ手順(自分用にコピーして使う方法)

### 1. このリポジトリをコピーする

このリポジトリページの右上にある緑色の **「Use this template」** ボタンを押し、
「Create a new repository」を選んで、自分のGitHubアカウントに新しいリポジトリとして複製してください。
(Public/Privateどちらでも構いません。Privateにしておくとより安全です)

### 2. MoodleのiCalエクスポートURLを取得する

1. 大学のMoodleにログインした状態で、以下のページにアクセスします。
   ```
   https://service.cloud.teu.ac.jp/moodle_epyc/calendar/export.php
   ```
2. 「エクスポートするもの」→ **すべてのイベント**
3. 「期間」→ **最近および次の60日間**
4. 一番下の **「認証キーを使ってエクスポート」** を選択し、「エクスポートする」ボタンを押す
5. 表示されたURL(`export_execute.php?...` から始まるもの)をコピーする
   - このURLには自分専用の秘密のトークンが含まれています。**他人に教えないでください**

### 3. DiscordのWebhook URLを取得する

1. 通知を送りたいDiscordサーバーのチャンネル設定を開く
2. 「連携サービス」→「ウェブフック」→「新しいウェブフック」を作成
3. 表示されたWebhook URLをコピーする

### 4. GitHubのSecretsに設定する

複製した自分のリポジトリで:

1. 上部メニューの **Settings** タブを開く
2. 左メニューの **Secrets and variables** → **Actions** を開く
3. **New repository secret** を押して、以下の2つを登録する

   | Name | Value |
   |---|---|
   | `ICAL_URL` | 手順2でコピーしたURL |
   | `DISCORD_WEBHOOK_URL` | 手順3でコピーしたURL |

### 5. GitHub Actionsを有効化する

1. リポジトリの **Actions** タブを開く
2. 「I understand my workflows, go ahead and enable them」のようなボタンが出ていたら押す
3. 左メニューから **Moodle Reminder** を選び、**Run workflow** を押すと手動で1回テスト実行できます

これで設定は完了です。以降は毎日 日本時間8:00 に自動実行され、締切3日以内に迫った課題がDiscordに通知されます。

## 設定のカスタマイズ

`.github/workflows/remind.yml` の中の以下の部分を編集することで挙動を変更できます。

- `cron: "0 23 * * *"` … 実行時刻(UTC基準。日本時間-9時間で指定)
- `REMIND_DAYS_BEFORE: "3"` … 締切何日前から通知するか

## 仕組み

- `remind.py` がMoodleのiCal URLにアクセスして課題一覧を取得します
- 締切が「今日から指定日数以内」かつ「まだ通知していない」課題だけをDiscordに送ります
- 通知済みの課題IDは `notified.json` に記録され、リポジトリに自動コミットされます(同じ課題を何度も通知しないため)

## 注意事項

- `ICAL_URL` には個人の認証トークンが含まれています。Secretsに登録すれば暗号化されてログにも表示されませんが、リポジトリ自体は念のためPrivateにすることをおすすめします
- Moodle側のiCalエクスポート設定が大学によって異なる場合は、URLの取得手順が多少異なることがあります
