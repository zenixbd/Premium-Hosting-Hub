# Premium Hosting Hub (Vercel + Runner)

এটি একটি starter project। Vercel-এ dashboard চলবে; আলাদা Linux VPS-এ Docker runner bot চালাবে। কোনো paid plan/payment feature নেই।

## Vercel
GitHub repository import করে Vercel deploy করুন। Project Settings → Environment Variables-এ যোগ করুন:
- `ADMIN_PASSWORD`: শক্তিশালী admin password
- `SESSION_SECRET`: লম্বা random secret (কমপক্ষে 32 অক্ষর)
- `RUNNER_URL`: runner-এর HTTPS URL, শেষে slash নয়
- `RUNNER_TOKEN`: runner-এর একই secret token
তারপর redeploy করুন।

## Runner VPS
Linux VPS-এ Docker Engine এবং Compose plugin ইনস্টল করুন। `runner/` ফোল্ডার VPS-এ কপি করে:
```bash
cd runner
cp .env.example .env
```
`.env`-এ শক্তিশালী `RUNNER_TOKEN` বসান। Vercel-এর `RUNNER_TOKEN`-এ একই মান দিন।
```bash
docker compose up -d --build
docker compose logs -f runner
```
Compose runner-কে `127.0.0.1:8080`-এ bind করে। HTTPS reverse proxy/domain সেট করে Vercel থেকে পৌঁছানোর ব্যবস্থা করুন। সরাসরি public port খুলবেন না।

## ZIP bot
ZIP-এর root-এ `main.py` অথবা `app.py` থাকতে হবে। `requirements.txt` ঐচ্ছিক। Bot foreground-এ চলতে হবে।

## নিরাপত্তা
এটি starter, production-audited নয়। Arbitrary ZIP চালানো বিপজ্জনক; Docker socket access root-equivalent। শুধু নিজের/বিশ্বস্ত code চালান, dedicated VPS ব্যবহার করুন, firewall/HTTPS/backups/monitoring যোগ করুন। Vercel নিজে 24/7 arbitrary bot runner নয়। Multi-user/billing নেই।
