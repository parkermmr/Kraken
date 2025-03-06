<style>
body {
    margin: 0;
    padding: 0;
    font-family: Arial, sans-serif;
    position: relative;
}

.watermark {
    position: fixed;
    top: 35%;
    left: 10%;
    width: 80%;
    text-align: center;
    font-size: 80px;
    font-weight: bold;
    color: rgba(255, 0, 0, 0.1); 
    transform: rotate(-30deg);
    z-index: -1;
    pointer-events: none;
}

.headerTitle {
  font-size: 45px;
  text-align: center;
}

.tab {
  display: inline-block;
  margin-left: 40px;
}

#backdrop {
  padding: 100 0 100 0;
  display: flex;
  justify-content: center;
  align-items: center;
}

.visually-hidden {
    clip: rect(0 0 0 0);
    clip-path: inset(100%);
    height: 1px;
    overflow: hidden;
    position: absolute;
    width: 1px;
    white-space: nowrap;
}

.toc-list, .toc-list ol {
  list-style-type: none;
}

.toc-list {
  padding: 0;
}

.toc-list ol {
  padding-inline-start: 2ch;
}

.toc-list > li > a {
  font-weight: bold;
  margin-block-start: 1em;
}

.toc-list li > a {
    text-decoration: none;
    display: grid;
    grid-template-columns: auto max-content;
    align-items: end;
}

.toc-list li > a > .title {
    position: relative;
    overflow: hidden;
}

.toc-list li > a .leaders::after {
    position: absolute;
    padding-inline-start: .25ch;
    content: " . . . . . . . . . . . . . . . . . . . "
        ". . . . . . . . . . . . . . . . . . . . . . . "
        ". . . . . . . . . . . . . . . . . . . . . . . "
        ". . . . . . . . . . . . . . . . . . . . . . . "
        ". . . . . . . . . . . . . . . . . . . . . . . "
        ". . . . . . . . . . . . . . . . . . . . . . . "
        ". . . . . . . . . . . . . . . . . . . . . . . ";
    text-align: right;
}

.toc-list li > a > .page {
    min-width: 2ch;
    font-variant-numeric: tabular-nums;
    text-align: right;
}
</style>

<div class="watermark">DRAFT</div>

<h1 id="headerTitle">Kraken Markdown</h1>

<h2>Table of Contents</h2>
<ol class="toc-list" role="list">
  <li>
    <a href="#Heading1">
      <span class="title">Heading 1<span class="leaders" aria-hidden="true"></span></span>
    </a>
        <ol role="list">
            <li>
                <a href="#SubHeading1">
                            <span class="title">Sub-Heading 1<span class="leaders" aria-hidden="true"></span>
                </a>
            </li>
        </ol>
    </li>
</ol>