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

function loadMoreHotUpdates() {
 const button = document.getElementById("load-more-hot-btn")
 const gridContainer = document.getElementById("manga-grid") // Match your HTML ID exactly!

 if (!button || !gridContainer) return

 const currentOffset = parseInt(button.getAttribute("data-next"))

 button.textContent = "Loading Updates..."
 button.disabled = true

 fetch(`/api/load-more-hot?offset=${currentOffset}`)
  .then((response) => response.text())
  .then((htmlContent) => {
   if (htmlContent.trim() === "") {
    button.textContent = "No More Results Available"
    button.style.display = "none"
    return
   }

   // Append new raw HTML elements directly inside the grid wrapper
   gridContainer.insertAdjacentHTML("beforeend", htmlContent)

   const nextOffset = currentOffset + 20
   button.setAttribute("data-next", nextOffset)

   button.textContent = "View More Results..."
   button.disabled = false
  })
  .catch((error) => {
   console.error("Error fetching more hot updates:", error)
   button.textContent = "Error Loading. Try Again."
   button.disabled = false
  })
}

function toggleBookmark(mangaId, mangaTitle, coverUrl) {
 const btn = document.getElementById(`bookmark-btn-${mangaId}`)
 const icon = document.getElementById(`bookmark-icon-${mangaId}`)

 // Prevent spam clicking
 if (btn.disabled) return
 btn.disabled = true

 fetch("/api/bookmark", {
  method: "POST",
  headers: {
   "Content-Type": "application/json",
  },
  body: JSON.stringify({
   manga_id: mangaId,
   manga_title: mangaTitle,
   cover_url: coverUrl,
  }),
 })
  .then((response) => {
   if (response.status === 401) {
    btn.disabled = false // Unlock the button

    const authModal = document.getElementById("auth-modal")
    if (authModal) {
     openAuth() // Just call your new function here!
    } else {
     alert("Please log in to bookmark manga.")
     window.location.href = "/login"
    }
    throw new Error("Unauthorized")
   }
   return response.json()
  })
  .then((data) => {
   if (data.status === "added") {
    icon.setAttribute("fill", "currentColor")
    btn.classList.add("text-orange-500")
    btn.classList.remove("text-gray-400", "hover:text-white")
   } else if (data.status === "removed") {
    icon.setAttribute("fill", "none")
    btn.classList.remove("text-orange-500")
    btn.classList.add("text-gray-400", "hover:text-white")
   }
   // Unlock button after a successful database save
   btn.disabled = false
  })
  .catch((error) => {
   console.error("Error toggling bookmark:", error)
   // Unlock button if something else goes wrong
   btn.disabled = false
  })
}

function openAuth() {
 const authModal = document.getElementById("auth-modal")
 if (authModal) {
  authModal.classList.remove("hidden")
  authModal.classList.add("flex") // Centers the modal
  document.body.style.overflow = "hidden" // Locks background scroll
 }
}

function closeAuth() {
 const authModal = document.getElementById("auth-modal")
 const modalContent = document.getElementById("auth-modal-content")

 if (authModal && modalContent) {
  // 1. Play "Out" animations
  authModal.classList.remove("animate-backdrop")
  authModal.classList.add("animate-backdrop-out")
  modalContent.classList.remove("animate-modal-pop")
  modalContent.classList.add("animate-modal-pop-out")

  // 2. Wait for animation, then hide and unlock scroll
  setTimeout(() => {
   authModal.classList.add("hidden")
   authModal.classList.remove("flex")

   document.body.style.overflow = "" // Unlocks background scroll!

   // 3. Reset classes for next time
   authModal.classList.remove("animate-backdrop-out")
   authModal.classList.add("animate-backdrop")
   modalContent.classList.remove("animate-modal-pop-out")
   modalContent.classList.add("animate-modal-pop")
  }, 200)
 }
}

async function removeBookmarkCard(mangaId) {
 // We call the same API route your "Add Bookmark" button uses
 const response = await fetch("/api/bookmark", {
  method: "POST",
  headers: {
   "Content-Type": "application/json",
  },
  body: JSON.stringify({ manga_id: mangaId }),
 })

 if (response.ok) {
  // Since the bookmark is deleted, we just reload the page
  // to show the updated list without that item
  location.reload()
 } else {
  alert("Failed to remove bookmark. Please try again.")
 }
}

function switchSettingsTab(tab) {
 // 1. Hide all sections
 document.getElementById("section-general").classList.add("hidden")
 document.getElementById("section-security").classList.add("hidden")

 // 2. Remove active style from all buttons
 const buttons = ["btn-general", "btn-security"]
 buttons.forEach((id) => {
  const btn = document.getElementById(id)
  btn.classList.remove("bg-orange-500/10", "text-orange-500")
  btn.classList.add("text-gray-500", "hover:text-white", "hover:bg-white/5")
 })

 // 3. Show selected section and activate button
 document.getElementById("section-" + tab).classList.remove("hidden")
 const activeBtn = document.getElementById("btn-" + tab)
 activeBtn.classList.add("bg-orange-500/10", "text-orange-500")
 activeBtn.classList.remove("text-gray-500", "hover:text-white", "hover:bg-white/5")
}
