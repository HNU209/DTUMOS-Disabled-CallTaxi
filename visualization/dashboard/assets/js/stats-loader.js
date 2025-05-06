// js/stats-loader.js
async function loadAndApplyStats() {
    // CSV 파일 경로
    const csvUrl = './assets/data/stats.csv';
  
    // CSV 파일 가져오기
    const res = await fetch(csvUrl);
    const text = await res.text();
  
    // 첫 줄은 헤더, 둘째 줄은 값으로 분리
    const [headerLine, dataLine] = text.trim().split('\n');
    const headers = headerLine.split(',');
    const values  = dataLine.split(',');
  
    // 헤더–값 매핑
    const stats = {};
    headers.forEach((h, i) => {
      stats[h.trim()] = values[i].trim();
    });
  
    // id가 있는 span에 값 적용
    document.getElementById('total-calls').textContent        = stats['total_calls'];
    document.getElementById('total-failed-calls').textContent = stats['failed_calls'];
    document.getElementById('failure-rate').textContent       = stats['failure_rate'];
    document.getElementById('vehicles-driven').textContent    = stats['vehicles_driven'];
  }
  
  // DOMContentLoaded 이벤트 발생 시 실행
  window.addEventListener('DOMContentLoaded', loadAndApplyStats);