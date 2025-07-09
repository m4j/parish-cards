#!/usr/bin/env python3

import hashlib
import os
import subprocess
import jinja2
import re

jinja_latex_env = jinja2.Environment(
    block_start_string='\BLOCK{',
    block_end_string='}',
    variable_start_string='\VAR{',
    variable_end_string='}',
    comment_start_string='\#{',
    comment_end_string='}',
    line_statement_prefix='%%',
    line_comment_prefix='%#',
    trim_blocks=True,
    autoescape=False,
    #loader=jinja2.FileSystemLoader(os.path.dirname(os.path.abspath(__file__))))
    #loader=jinja2.FileSystemLoader(os.getcwd()))
    loader=jinja2.PackageLoader(__name__, 'templates')
)

def escape_special_latex_characters(el_str):
    if isinstance(el_str, dict):
        return {k: escape_special_latex_characters(v) for k, v in el_str.items()}
    if isinstance(el_str, str):
        s = el_str.replace('$', '\\$')
        s = s.replace('<', '$<$')
        s = s.replace('>', '$>$')
        s = s.replace('#', '\\#')
        s = s.replace('_', '\\_')
        s = s.replace('&', '\\&')
        s = s.replace('\r\n', '\n\n')
        return s
    return el_str

def md_to_latex(string):
    string = re.sub(r"\*\*(.*)\*\*", r"\\textbf{\1}", string)
    return string


def compile_latex_to_pdf(tex_file_path, output_filename=None, timeout=60):
    """
    Compile a LaTeX file to PDF using XeLaTeX.

    Args:
        tex_file_path (str): Path to the .tex file to compile
        output_filename (str, optional): Name for the output PDF file. If None, uses the same name as tex_file_path
        timeout (int): Timeout in seconds for the compilation process

    Returns:
        bytes: The compiled PDF content as bytes

    Raises:
        subprocess.TimeoutExpired: If compilation times out
        subprocess.CalledProcessError: If compilation fails
        FileNotFoundError: If the output PDF file is not created
    """
    temp_dir = os.path.dirname(tex_file_path)
    tex_filename = os.path.basename(tex_file_path)
    base_name = os.path.splitext(tex_filename)[0]

    if output_filename:
        pdf_filename = output_filename
    else:
        pdf_filename = f"{base_name}.pdf"

    pdf_file_path = os.path.join(temp_dir, pdf_filename)
    aux_file_path = os.path.join(temp_dir, f"{base_name}.aux")

    # Compile LaTeX to PDF using XeLaTeX with MD5 hash checking
    previous_aux_hash = None
    max_runs = 5  # Prevent infinite loops

    for run in range(max_runs):
        # Run XeLaTeX
        result = subprocess.run(
            ['xelatex', '-halt-on-error', '-interaction=nonstopmode', tex_file_path],
            cwd=temp_dir,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        if result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode,
                ['xelatex', '-halt-on-error', '-interaction=nonstopmode', tex_file_path],
                result.stdout,
                result.stderr
            )

        # Check if .aux file exists and calculate its MD5 hash
        if os.path.exists(aux_file_path):
            with open(aux_file_path, 'rb') as f:
                current_aux_hash = hashlib.md5(f.read()).hexdigest()
        else:
            # If no .aux file exists, we're done (no cross-references to resolve)
            break

        # If this is the first run or the hash changed, continue
        if previous_aux_hash is None or current_aux_hash != previous_aux_hash:
            previous_aux_hash = current_aux_hash
            continue
        else:
            # Hash is the same as previous run, no more changes needed
            break

    # Check if PDF was created
    if not os.path.exists(pdf_file_path):
        raise FileNotFoundError(f"PDF compilation failed - no output file generated at {pdf_file_path}")

    # Read the generated PDF
    with open(pdf_file_path, 'rb') as f:
        return f.read()
