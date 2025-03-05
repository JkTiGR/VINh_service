document.addEventListener('DOMContentLoaded', function() {
    // ==============================
    // 1. Настройки Telegram (если нужно)
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
    // 4. Обновление дублированных полей (VIN, модель и т.д.)
    // ==============================
    function updateDuplicates() {
      const vinValue = document.getElementById("vin")?.value || "";
      const carModelValue = document.getElementById("carModel")?.value || "";
      const yearValue = document.getElementById("year")?.value || "";
      const plateValue = document.getElementById("plate")?.value || "";
  
      const vinDefects = document.getElementById("vin_defects");
      const carModelDefects = document.getElementById("carModel_defects");
      const yearDefects = document.getElementById("year_defects");
      const plateDefects = document.getElementById("plate_defects");
  
      const vinWork = document.getElementById("vin_work");
      const carModelWork = document.getElementById("carModel_work");
      const yearWork = document.getElementById("year_work");
      const plateWork = document.getElementById("plate_work");
  
      if (vinDefects) vinDefects.textContent = vinValue;
      if (carModelDefects) carModelDefects.textContent = carModelValue;
      if (yearDefects) yearDefects.textContent = yearValue;
      if (plateDefects) plateDefects.textContent = plateValue;
  
      if (vinWork) vinWork.textContent = vinValue;
      if (carModelWork) carModelWork.textContent = carModelValue;
      if (yearWork) yearWork.textContent = yearValue;
      if (plateWork) plateWork.textContent = plateValue;
    }
  
    // Привязываем обработчик ко всем нужным полям
    const vinField = document.getElementById("vin");
    const carModelField = document.getElementById("carModel");
    const yearField = document.getElementById("year");
    const plateField = document.getElementById("plate");
  
    if (vinField) {
      vinField.addEventListener("input", () => {
        vinField.value = vinField.value.toUpperCase();
        updateDuplicates();
      });
    }
    if (carModelField) carModelField.addEventListener("input", updateDuplicates);
    if (yearField) yearField.addEventListener("input", updateDuplicates);
    if (plateField) {
      plateField.addEventListener("input", () => {
        plateField.value = plateField.value.replace(/\s+/g, '').toUpperCase();
        updateDuplicates();
      });
    }
  
    // Первоначальный вызов (на случай, если поля уже заполнены)
    updateDuplicates();
  
    // ==============================
    // 5. Пересчёт общей суммы работ (в таблице work-table)
    // ==============================
    function recalcWorkTableForContainer(container) {
      const rows = container.querySelectorAll("table.work-table tbody tr");
      let total = 0;
      rows.forEach(row => {
        const partPriceEl = row.querySelector(".part-price");
        const workPriceEl = row.querySelector(".work-price");
        const partPrice = parseFloat(partPriceEl?.value) || 0;
        const workPrice = parseFloat(workPriceEl?.value) || 0;
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
      // Пересчёт суммы для work-table
      orderContainer.querySelectorAll(".part-price, .work-price").forEach(input => {
        input.addEventListener("input", () => {
          recalcWorkTableForContainer(orderContainer);
        });
      });
  
      // Кнопка "Додати рядок" (детали)
      orderContainer.querySelectorAll(".add-row-btn").forEach(btn => {
        btn.addEventListener("click", () => {
          const tableBody = orderContainer.querySelector("table.details-table tbody");
          if (!tableBody) return;
          const lastRow = tableBody.lastElementChild.cloneNode(true);
          // Номер строки = (текущее количество строк + 1)
          lastRow.cells[0].textContent = tableBody.rows.length + 1;
          // Очищаем значения
          lastRow.querySelectorAll("input[type='text']").forEach(el => el.value = "");
          lastRow.querySelectorAll("input[type='checkbox']").forEach(chk => chk.checked = false);
          tableBody.appendChild(lastRow);
        });
      });
  
      // Кнопка "Удалить строку" (детали)
      orderContainer.querySelectorAll(".remove-row-btn").forEach(btn => {
        btn.addEventListener("click", () => {
          const tableBody = orderContainer.querySelector("table.details-table tbody");
          if (!tableBody) return;
          // Удаляем последнюю строку, если их больше одной
          if (tableBody.rows.length > 1) {
            tableBody.removeChild(tableBody.lastElementChild);
          }
        });
      });
  
      // Кнопка "Додати рядок" (work-table)
      orderContainer.querySelectorAll(".add-work-row-btn").forEach(btn => {
        btn.addEventListener("click", () => {
          const tbody = orderContainer.querySelector("table.work-table tbody");
          if (!tbody) return;
          const newRow = tbody.lastElementChild.cloneNode(true);
          newRow.querySelectorAll("input").forEach(el => el.value = "");
          tbody.appendChild(newRow);
          // Повторно вешаем пересчёт суммы
          newRow.querySelectorAll(".part-price, .work-price").forEach(input => {
            input.addEventListener("input", () => {
              recalcWorkTableForContainer(orderContainer);
            });
          });
          recalcWorkTableForContainer(orderContainer);
        });
      });
  
      // Кнопка "Удалить строку" (work-table)
      orderContainer.querySelectorAll(".remove-work-row-btn").forEach(btn => {
        btn.addEventListener("click", () => {
          const tbody = orderContainer.querySelector("table.work-table tbody");
          if (!tbody) return;
          // Удаляем последнюю строку, если их больше одной
          if (tbody.rows.length > 1) {
            tbody.removeChild(tbody.lastElementChild);
          }
          // После удаления пересчитаем сумму
          recalcWorkTableForContainer(orderContainer);
        });
      });
  
      // Обнулить сумму при инициализации
      const workTotalElem = orderContainer.querySelector(".work-total");
      if (workTotalElem) {
        workTotalElem.textContent = "Общая сумма: 0";
      }
    }
  
    // ==============================
    // 7. Инициализация для оригинального заказа (первый .order)
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
          // Очищаем поля при копировании
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
          newOrder.appendChild(clone);
        }
      });
  
      // Кнопки внизу нового заказа
      const orderButtons = document.createElement("div");
      orderButtons.style.display = "flex";
      orderButtons.style.justifyContent = "space-between";
      orderButtons.style.marginTop = "10px";
  
      const saveBtn = document.createElement("button");
      saveBtn.type = "button";
      saveBtn.className = "btn btn-primary btn-small";
      saveBtn.textContent = "Сохранить";
      saveBtn.addEventListener("click", () => {
        alert("Новый наряд сохранён (реализуйте логику сохранения на сервере)");
      });
  
      const addOrderBtnClone = document.createElement("button");
      addOrderBtnClone.type = "button";
      addOrderBtnClone.className = "btn btn-primary btn-small";
      addOrderBtnClone.textContent = "добавить НАРЯД-ЗАМОВЛЕННЯ";
      addOrderBtnClone.addEventListener("click", addOrderHandler);
  
      orderButtons.appendChild(saveBtn);
      orderButtons.appendChild(addOrderBtnClone);
      newOrder.appendChild(orderButtons);
  
      // Сброс суммы
      const workTotalElem = newOrder.querySelector(".work-total");
      if (workTotalElem) {
        workTotalElem.textContent = "Общая сумма: 0";
      }
  
      document.querySelector("form").appendChild(newOrder);
      reinitializeOrderEventsForContainer(newOrder);
    }
  
    const addOrderBtn = document.getElementById("addOrderBtn");
    if (addOrderBtn) {
      addOrderBtn.addEventListener("click", addOrderHandler);
    }
  
    // ==============================
    // 9. Сбор данных формы и сохранение на сервере
    // ==============================
    function collectFormData() {
      const formData = {};
      document.querySelectorAll('form input, form textarea').forEach(el => {
        if (el.id) {
          if (el.type === 'checkbox') {
            formData[el.id] = el.checked;
          } else {
            formData[el.id] = el.value;
          }
        }
      });
      return formData;
    }
  
    function saveDashboardData() {
      const data = collectFormData();
      fetch("{{ url_for('vin_bp.submit_order') }}", {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
      .then(response => response.json())
      .then(result => {
        if (result.message) {
          alert('Данные успешно сохранены!');
        } else {
          alert('Ошибка сохранения: ' + (result.error || 'Неизвестная ошибка'));
        }
      })
      .catch(error => {
        console.error('Ошибка:', error);
        alert('Ошибка при сохранении данных.');
      });
    }
  
    const sendAdminBtn = document.getElementById('sendAdminBtn');
    if (sendAdminBtn) {
      sendAdminBtn.addEventListener('click', saveDashboardData);
    }
  
    // ==============================
    // 10. Загрузка данных дашборда с сервера по госномеру (GET /api/dashboard)
    // ==============================
    function loadDashboardData() {
      const plateEl = document.getElementById('plate');
      if (!plateEl) return;
      const plateVal = plateEl.value;
      if (plateVal) {
        fetch('/api/dashboard?plate=' + encodeURIComponent(plateVal))
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
      if (document.getElementById('plate')?.value) {
        loadDashboardData();
      }
    });
  
    // ==============================
    // 11. Отправка данных в Telegram (sendPartsBtn)
    // ==============================
    const sendPartsBtn = document.getElementById('sendPartsBtn');
    if (sendPartsBtn) {
      sendPartsBtn.addEventListener('click', function() {
        // Собираем данные из формы
        const clientName = document.getElementById('clientName')?.value || "";
        const phone = document.getElementById('phone')?.value || "";
        const vin = document.getElementById('vin')?.value || "";
        const carModel = document.getElementById('carModel')?.value || "";
        const year = document.getElementById('year')?.value || "";
        const plate = document.getElementById('plate')?.value || "";
        const mileage = document.getElementById('mileage')?.value || "";
        const workList = document.getElementById('workList')?.value || "";
  
        // Сбор индикаторов
        const indicators = [];
        const indicatorIds = ['checkEngine','battery','oil','coolant','tpms','airbag','abs','esp','brakeWear'];
        indicatorIds.forEach(id => {
          const el = document.getElementById(id);
          if (el && el.checked) {
            indicators.push(id);
          }
        });
  
        // Сбор названий запчастей из таблицы details-table
        const partNames = [];
        document.querySelectorAll("table.details-table tbody tr").forEach(row => {
          const input = row.querySelector("input[type='text']");
          if (input && input.value.trim() !== "") {
            partNames.push(input.value.trim());
          }
        });
  
        // Формируем сообщение
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
  
        // Отправляем сообщение через Telegram Bot API
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
    }
  
    // ==============================
    // 12. Функция autoGrow для <textarea>
    // ==============================
    function autoGrow(element) {
      element.style.height = 'auto';             // Сброс высоты
      element.style.height = element.scrollHeight + 'px';  // Подгоняем под содержимое
    }
  
    // Если хотите автоматически включить autoGrow для всех textarea:
    const allTextareas = document.querySelectorAll('textarea');
    allTextareas.forEach(tx => {
      // При вводе текста подгоняем высоту
      tx.addEventListener('input', () => autoGrow(tx));
      // Если изначально есть текст, подгоняем сразу
      if (tx.value.trim() !== '') {
        autoGrow(tx);
      }
    });
  });
  