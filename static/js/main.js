document.addEventListener('DOMContentLoaded', function() {
  // ==============================
  // 1. Настройки Telegram
  // ==============================
  const ADMIN_CHAT_ID = "-1002239976197";
  const BOT_TOKEN = "8099553216:AAEE3Ctou3yY4ddwVbXiUfHgfT7PeZyUyhA";

  // ==============================
  // 2. Логика бургер-меню
  // ==============================
  const menuButton = document.getElementById('menuButton');
  const sidebar = document.getElementById('sidebar');
  if (menuButton && sidebar) {
    menuButton.addEventListener('click', function(event) {
      event.stopPropagation();
      sidebar.classList.toggle('active');
    });
    document.addEventListener('click', function(event) {
      if (!sidebar.contains(event.target) && !menuButton.contains(event.target)) {
        sidebar.classList.remove('active');
      }
    });
  }

  // ==============================
  // 3. Обновление даты/времени
  // ==============================
  function updateDateTime() {
    const now = new Date();
    const formatted = now.toLocaleString();
    const dtVin = document.getElementById('dateTimeVin');
    const dtAct = document.getElementById('dateTimeAct');
    const dtWork = document.getElementById('dateTimeWork');
    if (dtVin) dtVin.textContent = formatted;
    if (dtAct) dtAct.textContent = formatted;
    if (dtWork) dtWork.textContent = formatted;
  }
  setInterval(updateDateTime, 1000);
  updateDateTime();

  // ==============================
  // 4. Обновление дублированных полей (VIN, модель, год, госномер)
  // ==============================
  function updateDuplicates() {
    const vinValue = document.getElementById("vin").value;
    const carModelValue = document.getElementById("carModel").value;
    const yearValue = document.getElementById("year").value;
    const plateValue = document.getElementById("plate").value;
    document.getElementById("vin_defects").textContent = vinValue;
    document.getElementById("carModel_defects").textContent = carModelValue;
    document.getElementById("year_defects").textContent = yearValue;
    document.getElementById("plate_defects").textContent = plateValue;
    document.getElementById("vin_work").textContent = vinValue;
    document.getElementById("carModel_work").textContent = carModelValue;
    document.getElementById("year_work").textContent = yearValue;
    document.getElementById("plate_work").textContent = plateValue;
  }
  document.getElementById("vin").addEventListener("input", updateDuplicates);
  document.getElementById("carModel").addEventListener("input", updateDuplicates);
  document.getElementById("year").addEventListener("input", updateDuplicates);
  document.getElementById("plate").addEventListener("input", updateDuplicates);
  updateDuplicates();

  // ==============================
  // 5. Пересчет общей суммы работ (work-table)
  // ==============================
  function recalcWorkTableForContainer(container) {
    const rows = container.querySelectorAll("table.work-table tbody tr");
    let total = 0;
    rows.forEach(row => {
      const partPrice = parseFloat(row.querySelector(".part-price").value) || 0;
      const workPrice = parseFloat(row.querySelector(".work-price").value) || 0;
      total += partPrice + workPrice;
    });
    const workTotalElem = container.querySelector(".work-total");
    if (workTotalElem) {
      workTotalElem.textContent = "Общая сумма: " + total.toFixed(2);
    }
  }

  // ==============================
  // 6. Инициализация обработчиков для одного "order"
  // ==============================
  function reinitializeOrderEventsForContainer(orderContainer) {
    orderContainer.querySelectorAll(".part-price, .work-price").forEach(input => {
      input.addEventListener("input", function() {
        recalcWorkTableForContainer(orderContainer);
      });
    });
    orderContainer.querySelectorAll(".add-row-btn").forEach(btn => {
      btn.addEventListener("click", function() {
        const tableBody = orderContainer.querySelector("table.details-table tbody");
        if (!tableBody) return;
        const lastRow = tableBody.lastElementChild.cloneNode(true);
        lastRow.cells[0].textContent = tableBody.rows.length + 1;
        lastRow.querySelectorAll("input[type='text']").forEach(input => input.value = "");
        lastRow.querySelectorAll("input[type='checkbox']").forEach(chk => chk.checked = false);
        tableBody.appendChild(lastRow);
      });
    });
    orderContainer.querySelectorAll(".add-work-row-btn").forEach(btn => {
      btn.addEventListener("click", function() {
        const tbody = orderContainer.querySelector("table.work-table tbody");
        if (!tbody) return;
        const newRow = tbody.lastElementChild.cloneNode(true);
        newRow.querySelectorAll("input").forEach(input => input.value = "");
        tbody.appendChild(newRow);
        newRow.querySelectorAll(".part-price, .work-price").forEach(input => {
          input.addEventListener("input", function() {
            recalcWorkTableForContainer(orderContainer);
          });
        });
        recalcWorkTableForContainer(orderContainer);
      });
    });
    orderContainer.querySelectorAll(".remove-row-btn").forEach(btn => {
      btn.addEventListener("click", function() {
        const tableBody = orderContainer.querySelector("table.details-table tbody");
        if (!tableBody) return;
        if (tableBody.rows.length > 1) {
          tableBody.removeChild(tableBody.lastElementChild);
        }
      });
    });
    orderContainer.querySelectorAll(".remove-work-row-btn").forEach(btn => {
      btn.addEventListener("click", function() {
        const tbody = orderContainer.querySelector("table.work-table tbody");
        if (!tbody) return;
        if (tbody.rows.length > 1) {
          tbody.removeChild(tbody.lastElementChild);
        }
        recalcWorkTableForContainer(orderContainer);
      });
    });
    const workTotalElem = orderContainer.querySelector(".work-total");
    if (workTotalElem) {
      workTotalElem.textContent = "Общая сумма: 0";
    }
  }

  // ==============================
  // 7. Инициализация для оригинального заказа
  // ==============================
  const originalOrder = document.querySelector(".order");
  if (originalOrder) {
    reinitializeOrderEventsForContainer(originalOrder);
  }

  // ==============================
  // 8. Клонирование заказа (добавление нового наряда)
  // ==============================
  function addOrderHandler() {
    const sectionIds = [
      "vinh-container",
      "indicators-container",
      "defects-container",
      "work-container",
      "control-signatures-container"
    ];
    const newOrder = document.createElement("div");
    newOrder.classList.add("order");
    sectionIds.forEach(id => {
      const section = document.getElementById(id);
      if (section) {
        const clone = section.cloneNode(true);
        clone.removeAttribute("id");
        if (id === "vinh-container") {
          const allowedNames = ["clientName", "phone", "vin", "carModel", "year", "plate"];
          clone.querySelectorAll("input, textarea").forEach(el => {
            if (!allowedNames.includes(el.name)) {
              el.value = "";
              if (el.type === "checkbox" || el.type === "radio") {
                el.checked = false;
              }
            }
          });
        } else {
          clone.querySelectorAll("input, textarea").forEach(el => {
            el.value = "";
            if (el.type === "checkbox" || el.type === "radio") {
              el.checked = false;
            }
          });
        }
        // Восстанавливаем исходный размер для workList и notes
        clone.querySelectorAll("textarea").forEach(el => {
          if (el.id === "workList" || el.id === "notes") {
            el.setAttribute("rows", "3");
            el.style.height = "";
          }
        });
        newOrder.appendChild(clone);
      }
    });
    const orderButtons = document.createElement("div");
    orderButtons.style.display = "flex";
    orderButtons.style.justifyContent = "space-between";
    orderButtons.style.marginTop = "10px";
    const saveBtn = document.createElement("button");
    saveBtn.type = "button";
    saveBtn.className = "btn btn-primary btn-small";
    saveBtn.textContent = "Сохранить";
    saveBtn.addEventListener("click", function() {
      alert("Новый наряд сохранён (функция сохранения должна быть реализована на сервере)");
    });
    const addOrderBtnClone = document.createElement("button");
    addOrderBtnClone.type = "button";
    addOrderBtnClone.className = "btn btn-primary btn-small";
    addOrderBtnClone.textContent = "добавить НАРЯД-ЗАМОВЛЕННЯ";
    addOrderBtnClone.addEventListener("click", addOrderHandler);
    orderButtons.appendChild(saveBtn);
    orderButtons.appendChild(addOrderBtnClone);
    newOrder.appendChild(orderButtons);
    const workTotalElem = newOrder.querySelector(".work-total");
    if (workTotalElem) {
      workTotalElem.textContent = "Общая сумма: 0";
    }
    document.querySelector("form").appendChild(newOrder);
    reinitializeOrderEventsForContainer(newOrder);
  }
  document.getElementById("addOrderBtn").addEventListener("click", addOrderHandler);

`Индикаторы: ${
  ['checkEngine', 'battery', 'oil', 'coolant', 'tpms', 'airbag', 'abs', 'esp', 'brakeWear']
    .filter(id => {
      const el = document.getElementById(id);
      return el && el.checked;
    })
    .map(id => {
      const names = {
        checkEngine: "Check Engine",
        battery: "Battery",
        oil: "Oil",
        coolant: "Coolant",
        tpms: "TPMS",
        airbag: "Airbag",
        abs: "ABS",
        esp: "ESP",
        brakeWear: "Brake Wear"
      };
      return names[id] || id;
    })
    .join(", ")
}\n\n`

  // ==============================
  // 10. Загрузка данных дашборда по госномеру
  // ==============================
  function loadDashboardData() {
    const plate = document.getElementById('plate').value;
    if (plate) {
      fetch('/api/dashboard?plate=' + encodeURIComponent(plate))
        .then(response => response.json())
        .then(data => {
          if (data.error) {
            console.log('Данные для данного госномера не найдены');
          } else {
            for (const key in data) {
              const element = document.getElementById(key);
              if (element) {
                if (element.type === 'checkbox') {
                  element.checked = data[key];
                } else {
                  element.value = data[key];
                }
              }
            }
            updateDuplicates();
          }
        })
        .catch(error => console.error('Ошибка загрузки данных:', error));
    }
  }
  window.addEventListener('load', function() {
    if (document.getElementById('plate').value) {
      loadDashboardData();
    }
  });

  // ==============================
  // 11. Отправка данных в Telegram (sendPartsBtn)
  // ==============================
  document.getElementById('sendPartsBtn').addEventListener('click', function() {
    const clientName = document.getElementById('clientName').value;
    const phone = document.getElementById('phone').value;
    const vin = document.getElementById('vin').value;
    const carModel = document.getElementById('carModel').value;
    const year = document.getElementById('year').value;
    const plate = document.getElementById('plate').value;
    const mileage = document.getElementById('mileage').value;
    const workList = document.getElementById('workList').value;
    const indicators = [];
    ['checkEngine','battery','oil','coolant','tpms','airbag','abs','esp','brakeWear'].forEach(id => {
      if(document.getElementById(id).checked) {
        indicators.push(id);
      }
    });
    const partNames = [];
    document.querySelectorAll("table.details-table tbody tr").forEach(row => {
      const input = row.querySelector("input[type='text']");
      if(input && input.value.trim() !== "") {
        partNames.push(input.value.trim());
      }
    });
    const message =
      `Имя клиента: ${clientName}\n` +
      `Телефон: ${phone}\n` +
      `VIN номер: ${vin}\n` +
      `Модель авто: ${carModel}\n` +
      `Год выпуска: ${year}\n` +
      `Номерний знак: ${plate}\n` +
      `Пробег (км): ${mileage}\n` +
      `Перечень желаемых работ: ${workList}\n` +
      `Индикаторы: ${indicators.join(", ")}\n` +
      `Назва запчастини або вузла: ${partNames.join(", ")}`;
    fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        chat_id: ADMIN_CHAT_ID,
        text: message
      })
    })
    .then(response => response.json())
    .then(data => {
      if (data.ok) {
        alert('Сообщение отправлено администратору!');
      } else {
        alert('Ошибка отправки: ' + data.description);
      }
    })
    .catch(error => {
      console.error('Ошибка при отправке сообщения:', error);
      alert('Ошибка при отправке данных.');
    });
  });

  // ==============================
  // 12. Функция autoGrow для <textarea>
  // ==============================
  function autoGrow(element) {
    element.style.height = 'auto';
    element.style.height = element.scrollHeight + 'px';
  }
  const allTextareas = document.querySelectorAll('textarea');
  allTextareas.forEach(tx => {
    tx.addEventListener('input', () => autoGrow(tx));
    if (tx.value.trim() !== '') {
      autoGrow(tx);
    }
  });
});
  
// Функция клонирования заказа (новый наряд)
function addOrderHandler() {
  const sectionIds = [
    "vinh-container",
    "indicators-container",
    "defects-container",
    "work-container",
    "control-signatures-container"
  ];
  const newOrder = document.createElement("div");
  newOrder.classList.add("order");
  sectionIds.forEach(id => {
    const section = document.getElementById(id);
    if (section) {
      const clone = section.cloneNode(true);
      clone.removeAttribute("id");
      if (id === "vinh-container") {
        const allowedNames = ["clientName", "phone", "vin", "carModel", "year", "plate"];
        clone.querySelectorAll("input, textarea").forEach(el => {
          if (!allowedNames.includes(el.name)) {
            el.value = "";
            if (el.type === "checkbox" || el.type === "radio") {
              el.checked = false;
            }
          }
        });
      } else {
        clone.querySelectorAll("input, textarea").forEach(el => {
          el.value = "";
          if (el.type === "checkbox" || el.type === "radio") {
            el.checked = false;
          }
        });
      }
      // Восстанавливаем исходный размер для workList и notes
      clone.querySelectorAll("textarea").forEach(el => {
        if (el.id === "workList" || el.id === "notes") {
          el.setAttribute("rows", "3");
          el.style.height = "";
        }
      });
      newOrder.appendChild(clone);
    }
  });
  const orderButtons = document.createElement("div");
  orderButtons.style.display = "flex";
  orderButtons.style.justifyContent = "space-between";
  orderButtons.style.marginTop = "10px";
  const saveBtn = document.createElement("button");
  saveBtn.type = "button";
  saveBtn.className = "btn btn-primary btn-small";
  saveBtn.textContent = "Сохранить";
  saveBtn.addEventListener("click", function() {
    alert("Новый наряд сохранён (функция сохранения должна быть реализована на сервере)");
  });
  const addOrderBtnClone = document.createElement("button");
  addOrderBtnClone.type = "button";
  addOrderBtnClone.className = "btn btn-primary btn-small";
  addOrderBtnClone.textContent = "добавить НАРЯД-ЗАМОВЛЕННЯ";
  addOrderBtnClone.addEventListener("click", addOrderHandler);
  orderButtons.appendChild(saveBtn);
  orderButtons.appendChild(addOrderBtnClone);
  newOrder.appendChild(orderButtons);
  const workTotalElem = newOrder.querySelector(".work-total");
  if (workTotalElem) {
    workTotalElem.textContent = "Общая сумма: 0";
  }
  document.querySelector("form").appendChild(newOrder);
  reinitializeOrderEventsForContainer(newOrder);
}
