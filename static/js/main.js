// CHAPTER TOGGLE
function toggleChapters() {
 const hiddenChapters = document.querySelectorAll(".chapter-item.hidden")
 const btn = document.getElementById("show-all-btn")
 hiddenChapters.forEach((chap) => chap.classList.remove("hidden"))
 if (btn) btn.remove()
}

// 1. AUTO-HIDE FLASH MESSAGES
setTimeout(() => {
 const alerts = document.querySelectorAll(".flash-alert")
 alerts.forEach((alert) => {
  alert.style.opacity = "0"
  setTimeout(() => alert.remove(), 1000)
 })
}, 4000)

// 2. ACCOUNT DROPDOWN LOGIC
function toggleAccountDropdown(event) {
 event.stopPropagation()
 const dropdown = document.getElementById("account-dropdown")
 const arrow = document.getElementById("dropdown-arrow")

 if (!dropdown) return

 const isOpen = dropdown.classList.contains("opacity-100")

 if (isOpen) {
  dropdown.classList.remove("opacity-100", "scale-100", "pointer-events-auto")
  dropdown.classList.add("opacity-0", "scale-95", "pointer-events-none")
  if (arrow) arrow.classList.remove("rotate-180")
 } else {
  dropdown.classList.remove("opacity-0", "scale-95", "pointer-events-none")
  dropdown.classList.add("opacity-100", "scale-100", "pointer-events-auto")
  if (arrow) arrow.classList.add("rotate-180")
 }
}

// 3. AUTH MODAL LOGIC
function openAuth() {
 const modal = document.getElementById("auth-modal")
 if (modal) {
  modal.classList.remove("hidden")
  document.body.style.overflow = "hidden"
 }
}

function closeAuth() {
 const modal = document.getElementById("auth-modal")
 if (modal) {
  modal.classList.add("hidden")
  document.body.style.overflow = "auto"
 }
}

function switchTab(tab) {
 const forms = ["login", "register", "forgot"]
 forms.forEach((f) => {
  const form = document.getElementById("form-" + f)
  const tabBtn = document.getElementById("tab-" + f)

  if (form) form.classList.add("hidden")
  if (tabBtn) {
   tabBtn.classList.remove("border-orange-500", "text-white")
   tabBtn.classList.add("text-gray-500", "border-transparent")
  }
 })

 const activeForm = document.getElementById("form-" + tab)
 const activeTab = document.getElementById("tab-" + tab)

 if (activeForm) activeForm.classList.remove("hidden")
 if (activeTab) {
  activeTab.classList.remove("text-gray-500", "border-transparent")
  activeTab.classList.add("border-orange-500", "text-white")
 }
}

// 4. GLOBAL CLICK HANDLER
window.onclick = function (event) {
 const modal = document.getElementById("auth-modal")
 const dropdown = document.getElementById("account-dropdown")
 const arrow = document.getElementById("dropdown-arrow")

 if (event.target == modal) closeAuth()

 if (dropdown && !dropdown.contains(event.target)) {
  dropdown.classList.remove("opacity-100", "scale-100", "pointer-events-auto")
  dropdown.classList.add("opacity-0", "scale-95", "pointer-events-none")
  if (arrow) arrow.classList.remove("rotate-180")
 }
}

window.addEventListener("scroll", () => {
 const btn = document.getElementById("back-to-top")
 if (window.scrollY > 500) {
  // Show the button (at 30% opacity like the original)
  btn.classList.remove("opacity-0", "pointer-events-none")
  btn.classList.add("opacity-30")
 } else {
  // Hide it completely
  btn.classList.add("opacity-0", "pointer-events-none")
  btn.classList.remove("opacity-30")
 }
})

// LIVE SEARCH SUGGESTIONS
const searchInput = document.getElementById("search-input")
const liveResults = document.getElementById("live-results")

if (searchInput) {
 searchInput.addEventListener("input", async (e) => {
  const query = e.target.value.trim()

  if (query.length < 2) {
   liveResults.classList.add("hidden")
   return
  }

  try {
   // Fetch results from your new API endpoint
   const response = await fetch(`/api/search_suggestions?q=${query}`)
   const data = await response.json()

   if (data.length > 0) {
    liveResults.innerHTML = data
     .map(
      (manga) => `
                    <a href="/manga/${manga.id}" class="flex items-center gap-3 p-3 hover:bg-white/5 border-b border-gray-800 last:border-none transition">
                        <img src="${manga.cover}" class="w-10 h-14 object-cover rounded shadow-md">
                        <div class="min-w-0">
                            <p class="text-xs font-bold text-white truncate">${manga.title}</p>
                            <p class="text-[10px] text-gray-500 uppercase tracking-tighter">${manga.author || "MangaDex Source"}</p>
                        </div>
                    </a>
                `,
     )
     .join("")
    liveResults.classList.remove("hidden")
   } else {
    liveResults.classList.add("hidden")
   }
  } catch (err) {
   console.error("Search failed:", err)
  }
 })

 // Hide results when clicking outside
 document.addEventListener("click", (e) => {
  if (!liveResults.contains(e.target) && e.target !== searchInput) {
   liveResults.classList.add("hidden")
  }
 })
}

// Toggle the Advanced Search Filter Menu
function toggleFilters() {
 const menu = document.getElementById("filter-menu")
 if (!menu) return

 // Toggle the height (0 rows to 1 full row)
 menu.classList.toggle("grid-rows-[0fr]")
 menu.classList.toggle("grid-rows-[1fr]")

 // Toggle the fade
 menu.classList.toggle("opacity-0")
 menu.classList.toggle("opacity-100")
}

async function loadMore() {
 const btn = document.getElementById("load-more-btn")
 const grid = document.getElementById("manga-grid")
 let nextOffset = btn.getAttribute("data-next")

 // If nextOffset is broken, default it to 36
 if (!nextOffset || nextOffset === "undefined" || nextOffset === "") {
  nextOffset = 36
 }

 btn.innerText = "Loading more..."
 btn.disabled = true

 const urlParams = new URLSearchParams(window.location.search)
 urlParams.set("offset", nextOffset)
 urlParams.set("ajax", "true")

 try {
  const response = await fetch(`/search?${urlParams.toString()}`)
  const html = await response.text()

  if (html.trim().length > 0) {
   grid.insertAdjacentHTML("beforeend", html)
   // Update for the next batch
   btn.setAttribute("data-next", parseInt(nextOffset) + 36)
   btn.innerText = "View More Results..."
   btn.disabled = false
  } else {
   btn.parentElement.remove() // No more manga, remove button
  }
 } catch (error) {
  btn.innerText = "Error. Try again?"
  btn.disabled = false
 }
}
