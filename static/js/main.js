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

// ==========================================
// ADVANCED SEARCH: 3-STATE TAG LOGIC
// ==========================================

// 1. Handle clicking the tags (Attached to the window so the HTML onclick can see it)
window.toggleTag = function (element) {
 let currentState = parseInt(element.getAttribute("data-state"))

 // Cycle: 0 (Neutral) -> 1 (Include) -> 2 (Exclude) -> 0
 let newState = (currentState + 1) % 3

 element.setAttribute("data-state", newState)
 element.className = `tag-btn tag-state-${newState} border rounded-md px-2.5 py-1.5 text-[10px] font-bold uppercase tracking-widest`
}

// 2. Intercept the form submission to attach the UUIDs
document.addEventListener("DOMContentLoaded", function () {
 const searchForm = document.getElementById("advanced-search-form")

 // Safety check: Only run this if we are actually on the Search page
 if (searchForm) {
  searchForm.addEventListener("submit", function (e) {
   // Remove any old hidden inputs so we don't duplicate them on multiple clicks
   document.querySelectorAll(".dynamic-tag").forEach((el) => el.remove())

   // Loop through every tag button on the screen
   document.querySelectorAll(".tag-btn").forEach((btn) => {
    let state = parseInt(btn.getAttribute("data-state"))
    let tagId = btn.getAttribute("data-id")

    if (state !== 0) {
     let input = document.createElement("input")
     input.type = "hidden"
     input.className = "dynamic-tag"
     // If state is 1, send to includedTags[]. If 2, send to excludedTags[]
     input.name = state === 1 ? "includedTags[]" : "excludedTags[]"
     input.value = tagId
     searchForm.appendChild(input)
    }
   })
   // Let the form submit naturally after injecting the hidden inputs
  })
 }
})

// ==========================================
// SUBSCRIPTION: PAYMENT MODAL LOGIC
// ==========================================

window.openPaymentModal = function () {
 const overlay = document.getElementById("payment-modal-overlay")
 const card = document.getElementById("payment-modal-card")

 // Safety check: Only run if the modal actually exists on the current page
 if (overlay && card) {
  overlay.classList.remove("opacity-0", "pointer-events-none")
  card.classList.remove("scale-95")
  card.classList.add("scale-100")
 }
}

window.closePaymentModal = function () {
 const overlay = document.getElementById("payment-modal-overlay")
 const card = document.getElementById("payment-modal-card")

 if (overlay && card) {
  overlay.classList.add("opacity-0", "pointer-events-none")
  card.classList.remove("scale-100")
  card.classList.add("scale-95")
 }
}

// ============================================================
//  POPULAR NEW TITLES — Hero Carousel (sliding, drag-follow, infinite)
//  Trượt ngang mượt: giữ chuột trái kéo theo con trỏ, thả ra nếu chưa
//  đủ ngưỡng thì trượt về chỗ cũ, đủ ngưỡng thì sang slide kế. Tự chạy.
// ============================================================
;(function () {
 const viewport = document.getElementById("hero-viewport")
 const track = document.getElementById("hero-track")
 if (!viewport || !track) return
 const slides = Array.from(track.querySelectorAll(".hero-slide"))
 const N = slides.length
 if (!N) return

 const bgA = document.getElementById("hero-bg")
 const bgB = document.getElementById("hero-bg2")
 const counter = document.getElementById("hero-counter")
 const btnPrev = document.getElementById("hero-prev")
 const btnNext = document.getElementById("hero-next")

 // --- Nhân bản 2 đầu để cuộn vòng vô hạn ---
 const firstClone = slides[0].cloneNode(true)
 const lastClone = slides[N - 1].cloneNode(true)
 track.appendChild(firstClone)
 track.insertBefore(lastClone, slides[0])
 // Track mở rộng: [lastClone, S0..S(N-1), firstClone] -> slide thật ở vị trí 1..N

 let pos = 1 // vị trí hiện tại trên track mở rộng
 let useA = true // lớp nền nào đang hiện
 const EASE = "transform .5s cubic-bezier(.22,.61,.36,1)"

 function W() {
  return viewport.clientWidth
 }
 function setX(px, anim) {
  track.style.transition = anim ? EASE : "none"
  track.style.transform = "translateX(" + px + "px)"
 }
 function settle(anim) {
  setX(-pos * W(), anim)
 }

 function realIndex() {
  if (pos === 0) return N - 1
  if (pos === N + 1) return 0
  return pos - 1
 }

 function updateMeta(instant) {
  const ri = realIndex()
  if (counter) counter.textContent = "NO. " + (ri + 1)
  const slide = slides[ri]
  const big = slide.getAttribute("data-cover")
  const small = slide.getAttribute("data-cover-sm")
  const incoming = useA ? bgB : bgA
  const outgoing = useA ? bgA : bgB
  const apply = (u) => {
   if (!u) return
   incoming.style.backgroundImage = 'url("' + u + '")'
   if (instant) {
    incoming.style.transition = "none"
   } else {
    incoming.style.transition = "opacity .6s ease"
    outgoing.style.transition = "opacity .6s ease"
   }
   incoming.style.opacity = "0.95"
   outgoing.style.opacity = "0"
   useA = !useA
  }
  if (big) {
   const probe = new Image()
   probe.onload = () => apply(big)
   probe.onerror = () => apply(small || big)
   probe.src = big
  } else {
   apply(small)
  }
 }

 function go(delta, anim) {
  pos += delta
  settle(anim !== false)
  updateMeta(false)
 }

 // Nhảy không hiệu ứng khi chạm slide nhân bản (tạo vòng lặp liền mạch)
 track.addEventListener("transitionend", () => {
  if (pos === 0) {
   pos = N
   settle(false)
  } else if (pos === N + 1) {
   pos = 1
   settle(false)
  }
 })

 // --- Khởi tạo ---
 // Preload ảnh nền slide đầu (cover_lg lớn) RỒI mới fade-in,
 // tránh hiện 1 nhịp nền trắng trong lúc trình duyệt đang tải ảnh.
 ;(function initBg() {
  if (!bgA) return
  bgA.style.opacity = "0"
  if (bgB) bgB.style.opacity = "0"

  const slide = slides[0]
  const big = slide.getAttribute("data-cover")
  const small = slide.getAttribute("data-cover-sm")

  const show = (url) => {
   if (!url) return
   bgA.style.backgroundImage = 'url("' + url + '")'
   // chờ trình duyệt apply background-image rồi mới fade lên,
   // để không thấy khung rỗng trong lúc đang vẽ.
   requestAnimationFrame(() => {
    bgA.style.transition = "opacity .35s ease"
    bgA.style.opacity = "0.95"
   })
  }

  if (big) {
   const probe = new Image()
   probe.onload = () => show(big)
   probe.onerror = () => show(small || big)
   probe.src = big
  } else if (small) {
   const probe = new Image()
   probe.onload = () => show(small)
   probe.onerror = () => show(small)
   probe.src = small
  }
 })()
 settle(false)
 if (counter) counter.textContent = "NO. 1"

 // --- Nút điều hướng ---
 if (btnNext)
  btnNext.addEventListener("click", (e) => {
   e.preventDefault()
   go(1)
   resetAuto()
  })
 if (btnPrev)
  btnPrev.addEventListener("click", (e) => {
   e.preventDefault()
   go(-1)
   resetAuto()
  })

 // --- Tự động chạy ---
 let timer = null
 function startAuto() {
  timer = setInterval(() => go(1), 6000)
 }
 function stopAuto() {
  if (timer) {
   clearInterval(timer)
   timer = null
  }
 }
 function resetAuto() {
  stopAuto()
  startAuto()
 }
 viewport.addEventListener("mouseenter", stopAuto)
 viewport.addEventListener("mouseleave", startAuto)
 document.addEventListener("visibilitychange", function () {
  if (document.hidden) {
   stopAuto() // Tab bị ẩn -> Dừng trượt
  } else {
   startAuto() // Mở lại tab -> Chạy trượt tiếp
  }
 })

 // --- Kéo-thả theo con trỏ ---
 let dragging = false,
  startX = 0,
  dx = 0
 viewport.addEventListener("mousedown", (e) => {
  if (e.button !== 0) return
  if (e.target.closest("#hero-prev, #hero-next")) return // để nút bấm hoạt động
  dragging = true
  startX = e.clientX
  dx = 0
  stopAuto()
  setX(-pos * W(), false)
  e.preventDefault()
 })
 window.addEventListener("mousemove", (e) => {
  if (!dragging) return
  dx = e.clientX - startX
  // nhẹ tay ở hai đầu (đỡ giật) — vẫn cho kéo vì có clone
  setX(-pos * W() + dx, false)
 })
 window.addEventListener("mouseup", () => {
  if (!dragging) return
  dragging = false
  const TH = Math.min(120, W() * 0.15)
  if (dx <= -TH) go(1)
  else if (dx >= TH) go(-1)
  else settle(true) // chưa đủ ngưỡng -> trượt về chỗ cũ
  startAuto()
 })

 // Chặn click điều hướng link khi vừa kéo (tránh bấm nhầm vào truyện)
 viewport.addEventListener(
  "click",
  (e) => {
   if (Math.abs(dx) > 6) {
    e.preventDefault()
    e.stopPropagation()
   }
  },
  true,
 )

 // Tính lại khi đổi kích thước cửa sổ
 window.addEventListener("resize", () => settle(false))
})()

// ============================================================
//  READER SETTINGS — dán khối này vào CUỐI main.js
//  Quản lý 4 mode đọc (single/double/long/wide), reading direction,
//  header visibility, progress bar position. Lưu bằng localStorage.
// ============================================================
;(function () {
 const container = document.getElementById("reader-image-container")
 if (!container) return // chỉ chạy trên trang reader

 const KEY = "mangalocal_reader_prefs"
 const defaults = {
  display: "long", // single | double | long | wide
  dir: "ltr", // ltr | rtl
  header: "shown", // shown | hidden
  progress: "bottom", // hidden | bottom | left | right
 }
 let prefs = Object.assign({}, defaults)
 try {
  const saved = JSON.parse(localStorage.getItem(KEY))
  if (saved) prefs = Object.assign(prefs, saved)
 } catch (e) {}

 const images = Array.from(container.querySelectorAll("img"))
 let pageIndex = 0 // trang hiện tại cho single/double

 function savePrefs() {
  try {
   localStorage.setItem(KEY, JSON.stringify(prefs))
  } catch (e) {}
 }

 // ---------- Áp dụng chế độ hiển thị ----------
 function applyDisplay() {
  container.classList.remove("mode-wide", "mode-paged", "dir-rtl")
  images.forEach((img) => {
   img.classList.remove("page-visible")
   img.style.display = ""
  })

  // Ẩn khối "hết chương / quảng cáo" khi ở single/double/wide để không vướng thao tác click lật trang
  const extras = document.querySelectorAll("[data-reader-extra]")
  const isPagedOrWide = prefs.display === "single" || prefs.display === "double" || prefs.display === "wide"
  extras.forEach((el) => {
   el.style.display = isPagedOrWide ? "none" : ""
  })

  if (prefs.display === "long") {
   // cuộn dọc — hiện tất cả ảnh (mặc định)
   images.forEach((img) => (img.style.display = "block"))
  } else if (prefs.display === "wide") {
   images.forEach((img) => (img.style.display = "block"))
   container.classList.add("mode-wide")
   if (prefs.dir === "rtl") container.classList.add("dir-rtl")
  } else {
   // single hoặc double: ẩn hết, chỉ hiện trang hiện tại
   container.classList.add("mode-paged")
   if (prefs.dir === "rtl") container.classList.add("dir-rtl")
   showPages()
  }
  updateProgress()
 }

 function showPages() {
  images.forEach((img) => img.classList.remove("page-visible"))
  if (prefs.display === "single") {
   if (images[pageIndex]) images[pageIndex].classList.add("page-visible")
  } else if (prefs.display === "double") {
   let a = pageIndex,
    b = pageIndex + 1
   const order = prefs.dir === "rtl" ? [b, a] : [a, b]
   order.forEach((i) => {
    if (images[i]) images[i].classList.add("page-visible")
   })
  }
 }

 function maxIndex() {
  return prefs.display === "double" ? Math.max(0, images.length - 2) : Math.max(0, images.length - 1)
 }
 function step() {
  return prefs.display === "double" ? 2 : 1
 }

 function nextPage() {
  pageIndex = Math.min(pageIndex + step(), maxIndex())
  showPages()
  updateProgress()
  window.scrollTo({ top: 0 })
 }
 function prevPage() {
  pageIndex = Math.max(pageIndex - step(), 0)
  showPages()
  updateProgress()
  window.scrollTo({ top: 0 })
 }

 // ---------- Click trái/phải cho single & double ----------
 container.addEventListener("click", (e) => {
  if (prefs.display !== "single" && prefs.display !== "double") return
  const x = e.clientX
  const leftSide = x < window.innerWidth / 2
  // ltr: trái=lùi, phải=tiếp ; rtl: ngược lại
  if (prefs.dir === "ltr") {
   leftSide ? prevPage() : nextPage()
  } else {
   leftSide ? nextPage() : prevPage()
  }
 })

 // ---------- Wide strip: giữ chuột trái ở mép để cuộn ngang (không quá nhanh) ----------
 let wideHold = null
 container.addEventListener("mousedown", (e) => {
  if (prefs.display !== "wide" || e.button !== 0) return
  const leftSide = e.clientX < window.innerWidth / 2
  // ltr: phải=tiếp(cuộn xuôi), trái=lùi ; rtl thì đảo
  let forward = prefs.dir === "ltr" ? !leftSide : leftSide
  const dirSign = forward ? 1 : -1
  // tốc độ vừa phải: 8px mỗi ~16ms
  wideHold = setInterval(() => {
   container.scrollLeft += dirSign * 8
   updateProgress()
  }, 16)
 })
 function stopWide() {
  if (wideHold) {
   clearInterval(wideHold)
   wideHold = null
  }
 }
 container.addEventListener("mouseup", stopWide)
 container.addEventListener("mouseleave", stopWide)

 // ---------- Progress bar ----------
 const wrap = document.getElementById("reader-progress-wrap")
 const bar = document.getElementById("reader-progress-bar")
 function applyProgressPos() {
  if (!wrap) return
  wrap.setAttribute("data-pos", prefs.progress)
 }
 function updateProgress() {
  if (!wrap || !bar || prefs.progress === "hidden") return
  let pct = 0
  if (prefs.display === "long") {
   const h = document.documentElement.scrollHeight - window.innerHeight
   pct = h > 0 ? (window.scrollY / h) * 100 : 0
  } else if (prefs.display === "wide") {
   const w = container.scrollWidth - container.clientWidth
   pct = w > 0 ? (Math.abs(container.scrollLeft) / w) * 100 : 0
  } else {
   pct = maxIndex() > 0 ? (pageIndex / maxIndex()) * 100 : 100
  }
  pct = Math.max(0, Math.min(100, pct))
  if (prefs.progress === "bottom") bar.style.width = pct + "%"
  else bar.style.height = pct + "%"
 }
 window.addEventListener("scroll", updateProgress)

 // ---------- Header visibility ----------
 function applyHeader() {
  const hide = prefs.header === "hidden"
  document.querySelectorAll("[data-reader-header]").forEach((el) => {
   el.style.display = hide ? "none" : ""
  })
  // Khi header bị ẩn, hiện một nút bánh răng nổi để vẫn mở lại được Reader Settings
  let fab = document.getElementById("reader-fab-settings")
  if (hide) {
   if (!fab) {
    fab = document.createElement("button")
    fab.id = "reader-fab-settings"
    fab.type = "button"
    fab.title = "Reader Settings"
    fab.setAttribute("aria-label", "Reader Settings")
    fab.onclick = function () {
     window.openReaderSettings()
    }
    fab.style.cssText = "position:fixed;top:12px;right:12px;z-index:55;padding:10px;border-radius:9999px;" + "background:rgba(30,30,30,.85);color:#f97316;border:1px solid #3a3a3a;cursor:pointer;" + "box-shadow:0 4px 14px rgba(0,0,0,.4);backdrop-filter:blur(4px);transition:opacity .2s;"
    fab.innerHTML =
     '<svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24">' +
     '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>' +
     '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>'
    document.body.appendChild(fab)
   }
   fab.style.display = "block"
  } else if (fab) {
   fab.style.display = "none"
  }
 }

 // ---------- Cập nhật trạng thái nút trong popup ----------
 function syncButtons() {
  const map = [
   [".rs-display", prefs.display],
   [".rs-dir", prefs.dir],
   [".rs-header", prefs.header],
   [".rs-progress", prefs.progress],
  ]
  map.forEach(([sel, val]) => {
   document.querySelectorAll(sel).forEach((b) => {
    b.classList.toggle("rs-active", b.getAttribute("data-val") === val)
   })
  })
 }

 // ---------- Gắn sự kiện cho các nút popup ----------
 function bindGroup(sel, field, after) {
  document.querySelectorAll(sel).forEach((btn) => {
   btn.addEventListener("click", () => {
    prefs[field] = btn.getAttribute("data-val")
    if (field === "display") pageIndex = 0
    savePrefs()
    syncButtons()
    if (after) after()
   })
  })
 }
 bindGroup(".rs-display", "display", applyDisplay)
 bindGroup(".rs-dir", "dir", applyDisplay)
 bindGroup(".rs-header", "header", applyHeader)
 bindGroup(".rs-progress", "progress", () => {
  applyProgressPos()
  updateProgress()
 })

 // ---------- Mở / đóng popup (fade in/out) ----------
 window.openReaderSettings = function () {
  const ov = document.getElementById("reader-settings-overlay")
  const card = document.getElementById("reader-settings-card")
  if (!ov) return
  syncButtons()
  ov.classList.remove("opacity-0", "pointer-events-none")
  ov.classList.add("opacity-100")
  if (card) {
   card.classList.remove("scale-95")
   card.classList.add("scale-100")
  }
  document.body.style.overflow = "hidden"
 }
 window.closeReaderSettings = function () {
  const ov = document.getElementById("reader-settings-overlay")
  const card = document.getElementById("reader-settings-card")
  if (!ov) return
  ov.classList.add("opacity-0", "pointer-events-none")
  ov.classList.remove("opacity-100")
  if (card) {
   card.classList.add("scale-95")
   card.classList.remove("scale-100")
  }
  document.body.style.overflow = ""
 }

 // ---------- Khởi tạo ----------
 applyProgressPos()
 applyDisplay()
 applyHeader()
 syncButtons()
})()

// ============================================================
//  NAV TRONG SUỐT Ở TRANG CHỦ (lộ ảnh nền carousel xuyên qua header)
//  Chỉ chạy khi có carousel (#popular-hero) -> không ảnh hưởng trang khác.
//  Ở đỉnh trang: nav trong suốt. Cuộn xuống quá ngưỡng: nav có nền đặc lại.
// ============================================================
;(function () {
 const hero = document.getElementById("popular-hero")
 if (!hero) return // trang khác không có carousel -> bỏ qua, nav giữ nền mặc định

 const THRESHOLD = 180 // px cuộn trước khi nav chuyển sang nền đặc
 function onScroll() {
  if (window.scrollY < THRESHOLD) {
   document.body.classList.add("nav-transparent")
  } else {
   document.body.classList.remove("nav-transparent")
  }
 }
 onScroll() // set trạng thái ban đầu
 window.addEventListener("scroll", onScroll, { passive: true })
})()

// ============================================================
//  NAV TRONG SUỐT Ở TRANG TRUYỆN (lộ ảnh nền mờ xuyên qua header)
//  Tự động quét thẻ chứa ảnh nền mờ đặc trưng của manga.html
// ============================================================
;(function () {
 // Tìm khối div nền mờ dựa vào các class Tailwind đặc trưng của trang manga
 const mangaBg = document.querySelector(".pointer-events-none.fixed.inset-x-0.top-0.z-0")

 // Nếu không tìm thấy (nghĩa là đang ở trang khác) -> Dừng chạy, giữ nguyên nền đen mặc định
 if (!mangaBg) return

 // Ngưỡng px cuộn xuống trước khi nav chuyển sang nền đặc
 // (mình để 60px cho trang truyện vì không có carousel to như trang chủ)
 const THRESHOLD = 60

 function onScroll() {
  if (window.scrollY < THRESHOLD) {
   document.body.classList.add("nav-transparent")
  } else {
   document.body.classList.remove("nav-transparent")
  }
 }

 // Thiết lập trạng thái ngay khi vừa load trang
 onScroll()

 // Lắng nghe sự kiện cuộn chuột
 window.addEventListener("scroll", onScroll, { passive: true })
})()

// ============================================================
//  ĐĂNG KÝ SUPPORTER — hiện popup cảm ơn thay vì redirect
// ============================================================
;(function () {
 const form = document.querySelector("#payment-modal-card form")
 if (!form) return
 form.addEventListener("submit", function (e) {
  e.preventDefault()
  if (!form.checkValidity()) {
   form.reportValidity()
   return
  }
  const btn = form.querySelector('button[type="submit"]')
  const orig = btn ? btn.textContent : ""
  if (btn) {
   btn.disabled = true
   btn.textContent = "Đang xử lý..."
  }
  fetch("/api/upgrade", { method: "POST", headers: { "X-Requested-With": "fetch" } })
   .then(function () {
    if (window.closePaymentModal) window.closePaymentModal()
    const ov = document.getElementById("success-modal-overlay")
    const card = document.getElementById("success-modal-card")
    if (ov && card) {
     ov.classList.remove("opacity-0", "pointer-events-none")
     card.classList.remove("scale-95")
     card.classList.add("scale-100")
    } else {
     window.location.href = "/setting"
    }
   })
   .catch(function () {
    window.location.href = "/setting"
   })
   .finally(function () {
    if (btn) {
     btn.disabled = false
     btn.textContent = orig
    }
   })
 })
})()
// ============================================================
//  ĐIỀU KHIỂN MENU MOBILE (HAMBURGER)
// ============================================================
;(function () {
 const mobileBtn = document.getElementById("mobile-menu-btn")
 const navMenu = document.getElementById("nav-menu")

 if (mobileBtn && navMenu) {
  mobileBtn.addEventListener("click", function () {
   // Toggle giữa class ẩn (hidden) và class hiện (flex)
   navMenu.classList.toggle("hidden")
  })
 }
})()
