FROM python:3.14-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# XeLaTeX plus the packages used by the report templates, and Liberation
# so fontspec can resolve \setmainfont{Liberation Sans}.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        fontconfig \
        fonts-liberation \
        texlive-xetex \
        texlive-latex-extra \
        texlive-plain-generic \
        texlive-lang-cyrillic \
    && fc-cache -f \
    && rm -rf /var/lib/apt/lists/* \
    && fc-list : family | grep -F "Liberation Sans"

# Fail the image build if the report preamble cannot compile with Liberation Sans.
RUN cat > /tmp/fontcheck.tex <<'EOF'
\documentclass{article}
\usepackage[margin=1in]{geometry}
\usepackage[utf8]{inputenc}
\usepackage[russian,english]{babel}
\usepackage[useregional]{datetime2}
\usepackage{multicol}
\usepackage{longtable}
\usepackage{booktabs}
\usepackage{fontspec}
\setmainfont{Liberation Sans}
\usepackage{sectsty}
\usepackage{tocloft}
\usepackage[table]{xcolor}
\usepackage{multirow}
\usepackage{bigdelim}
\usepackage{arydshln}
\begin{document}
Hello Привет
\end{document}
EOF
RUN xelatex -halt-on-error -interaction=batchmode -output-directory=/tmp /tmp/fontcheck.tex \
    || { cat /tmp/fontcheck.log; exit 1; } \
    && rm -f /tmp/fontcheck.*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY parish.py member.py gunicorn.conf.py ./
COPY app ./app
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh \
    && mkdir -p /data

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "-c", "gunicorn.conf.py", "parish:app"]
