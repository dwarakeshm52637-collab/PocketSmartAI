async function api(
    url,
    options = {}
) {

    const headers =
        options.headers || {};


    if (
        options.body &&
        !(options.body instanceof FormData)
    ) {

        headers["Content-Type"] =
            "application/json";
    }


    const response =
        await fetch(
            url,
            {
                ...options,
                headers,
                credentials:
                    "same-origin"
            }
        );


    let data = {};

    try {

        data =
            await response.json();

    } catch (e) {}


    return {
        ok: response.ok,
        status: response.status,
        data
    };
}


function escapeHtml(v) {

    return String(
        v ?? ""
    ).replace(
        /[&<>"']/g,
        c => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#039;"
        }[c])
    );
}


function renderResult(r) {

    const target =
        document.querySelector(
            "#result"
        );


    if (!r.ok) {

        if (r.status === 401) {

            location.href =
                "/login";

            return;
        }


        target.innerHTML =
            `<div class="empty">
                ${escapeHtml(
                    r.data.detail ||
                    "Something went wrong."
                )}
            </div>`;

        return;
    }


    const x = r.data;


    const items =
        (x.items || [])
        .map(
            i => `

<article class="item">

<div class="item-top">

<strong>
${escapeHtml(i.name)}
</strong>

<span class="pill">
${escapeHtml(i.platform)}
</span>

</div>


<p>
${escapeHtml(i.reason)}
</p>


<b>
Estimated: ₹${Number(
    i.estimated_price || 0
).toLocaleString("en-IN")}
</b>

<br>


<a
    href="${escapeHtml(i.search_url)}"
    target="_blank"
    rel="noopener"
>
Search on
${escapeHtml(i.platform)}
↗
</a>

</article>

`
        )
        .join("");


    const plan =
        (x.budget_plan || [])
        .map(
            p => `

<div>

<div class="item-top">

<span>
${escapeHtml(p.category)}
</span>

<b>
${Number(
    p.percentage
).toFixed(0)}%
</b>

</div>


<div class="bar">

<i
    style="width:${Math.min(
        100,
        Math.max(
            0,
            Number(
                p.percentage
            )
        )
    )}%"
></i>

</div>

</div>

<br>

`
        )
        .join("");


    target.innerHTML = `

<section class="result">

<h2>
${escapeHtml(x.title)}
</h2>

<p>
${escapeHtml(x.summary)}
</p>


<div class="result-grid">

<div>
${items}
</div>


<aside class="budget-box">

<h3>
Budget allocation
</h3>

${plan}

</aside>

</div>

</section>

`;

}


(async()=>{

    const login =
        document.querySelector(
            "#loginLink"
        );

    const logout =
        document.querySelector(
            "#logoutBtn"
        );


    if (
        !login ||
        !logout
    ) {
        return;
    }


    const r =
        await api(
            "/session-info"
        );


    if (r.ok) {

        login.hidden =
            true;

        logout.hidden =
            false;


        logout.onclick =
            async () => {

                await api(
                    "/logout",
                    {
                        method:
                            "POST"
                    }
                );

                location.href =
                    "/";
            };
    }

})();