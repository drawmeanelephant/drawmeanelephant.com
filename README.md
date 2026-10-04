# drawmeanelephant.com 🐘

Welcome to the static site repository for **[drawmeanelephant.com](https://www.drawmeanelephant.com)**. 

This repository archives the Draw Me An Elephant correspondence project: letters to breweries and other places, the drawings and replies that came back, WordPress updates, and miscellaneous Instagram takeouts.

Built using **Boris**, the ultra-fast and strict static site compiler.

***

## 📁 Repository Structure

We maintain a clean separation of the website's source material and the public production assets:

*   **`main` Branch**: Contains the website's source content (all 900+ markdown files, local polaroid drawings, and assets), custom handcrafted theme layout/styles, and local compile binaries.
*   **`gh-pages` Branch**: GitHub Pages is also enabled for this repository and serves the root of this branch at `https://drawmeanelephant.github.io/drawmeanelephant.com/`. The automated Cloudflare Pages workflow described below does not update this branch.

### Folder Tour
```
.
├── bin/
│   └── boris                     # Local compiler binary
├── content/                      # 900+ raw structured Markdown source files
│   ├── index.md                  # Homepage index file
│   ├── breweries.md              # Main Directory section page
│   ├── posts.md                  # Blog Updates section page
│   ├── instagram.md              # Instagram section page
│   ├── breweries/                # Individual brewery trunk pages (138 total)
│   ├── posts/                    # Blog post updates
│   └── instagram/                # Unmapped Instagram photo archives
├── themes/
│   └── drawmeanelephant/         # Handcrafted custom parchment theme
│       ├── footer.html           # Cool sketchy footer
│       ├── layouts/main.html     # Base HTML layout skeleton
│       └── assets/               # Main theme stylesheet
├── .gitignore
├── build.sh                      # One-click build script
└── README.md
```

***

## 🎨 Theme Design: "Golden Sketchbook"

The website is rendered using a handcrafted theme, **`drawmeanelephant`**, designed specifically to mirror the hand-drawn, cozy, and humorous nature of the original project:

*   **Color Palette**: Uses warm cream sketchbook parchment backgrounds (`#fdfaf4`), lively sketchy orange primary accents (`#ff661a`), mustard/golden-yellow header and details backgrounds (`#e2aa36`), and soft pencil graphite charcoal body text (`#2d2621`).
*   **Wavy Hand-Drawn Borders**: Cards, polaroids, tables, and buttons feature organic, uneven border sketches utilizing CSS border tricks:
    `border-radius: 255px 15px 225px 15px/15px 225px 15px 255px;`
*   **Collapsible Sidebar Navigation**: Implemented with pure CSS `:has()` pseudo-selector to automatically expand only the active section directory lists, keeping the index list perfectly clean.
*   **Micro-Animations**: Polaroids, navigation links, and highlights tilt and scale organically on hover (`transform: scale(1.02) rotate(-1deg)`), making the site feel tactile and responsive.
*   **Tagline Footer**: Displays the iconic project closure: `COOL. I GUESS. 🐘`.

***

## 🛠️ How to Build and Run Locally

### Requirements
A Mac/Unix shell with execution permissions.

### Step 1: Clone the Repository
```bash
git clone https://github.com/drawmeanelephant/drawmeanelephant.com.git
cd drawmeanelephant.com
```

### Step 2: Build the Site
Run the local compile script to build the markdown source and copy theme assets into the `dist/` directory:
```bash
chmod +x build.sh
./build.sh
```

### Step 3: View Locally
Once built, open `dist/index.html` in any web browser to view the site, or run a lightweight local dev server:
```bash
cd dist
python3 -m http.server 8000
```
Then visit `http://localhost:8000` in your browser.

***

## 🚀 Deployment (Cloudflare Pages)

The checked-in GitHub Actions workflow in `.github/workflows/deploy.yml` builds and deploys the site to the Cloudflare Pages project `drawmeanelephant`.

The workflow runs when a commit is pushed to `main` or `master`, when a pull request targets either branch, or when someone starts it with the `workflow_dispatch` button in GitHub Actions. For each run, it checks out this repository on an Ubuntu 24.04 runner, builds Boris from the `afterparty` branch of `drawmeanelephant/boris` with Zig 0.16.0, and runs `./build.sh` to create the static site in `dist/`. The workflow then deploys `dist/` using Wrangler's `pages deploy` command.

The separate `.github/workflows/ci.yml` workflow runs on pushes and pull requests targeting `main` or `master`. It performs the build and uploads `dist/` as the `site-dist` artifact; it does not deploy the site.

The deploy job reads the `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` GitHub Actions secrets. Make both secrets available to the workflow for deployments to succeed; their values are not stored in this repository.

GitHub Pages is separately configured to serve the `gh-pages` branch from its root. The Cloudflare workflow does not push to or update that branch.

*Enjoy exploring the elephants! 🐘*
