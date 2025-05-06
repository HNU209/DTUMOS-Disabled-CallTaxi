// function openCity(evt, cityName) {
//     // Declare all variables
//     var i, tabcontent, tablinks;
  
//     // Get all elements with class="tabcontent" and hide them
//     tabcontent = document.getElementsByClassName("tabcontent");
//     for (i = 0; i < tabcontent.length; i++) {
//         tabcontent[i].style.display = "none";
//     }
  
//     // Get all elements with class="tablinks" and remove the class "active"
//     tablinks = document.getElementsByClassName("tablinks");
//     for (i = 0; i < tablinks.length; i++) {
//         tablinks[i].className = tablinks[i].className.replace(" active", "");
//     }
  
//     // Show the current tab, and add an "active" class to the button that opened the tab
//     document.getElementById(cityName).style.display = "flex";
//     evt.currentTarget.className += " active";
// }

// const openImg = fig => {
//     window.open(`./assets/${fig}.html`);
// }

function openCity(evt, cityName) {
    // 1) 모든 탭 숨기기
    const tabcontent = document.getElementsByClassName("tabcontent");
    for (let i = 0; i < tabcontent.length; i++) {
      tabcontent[i].style.display = "none";
    }
    // 2) 버튼 active 해제
    const tablinks = document.getElementsByClassName("tablinks");
    for (let i = 0; i < tablinks.length; i++) {
      tablinks[i].classList.remove("active");
    }
    // 3) 현재 탭 보이기 + 버튼 active
    const cur = document.getElementById(cityName);
    cur.style.display = "flex";
    evt.currentTarget.classList.add("active");
  
    // 4) 보인 탭의 iframe data-src → src로 옮겨서 로드 강제
    cur.querySelectorAll("iframe[data-src]").forEach(frame => {
      // 최초 로드만 하고 싶으면 if(!frame.src) 로 감싸세요
      frame.src = frame.dataset.src;
    });
  }