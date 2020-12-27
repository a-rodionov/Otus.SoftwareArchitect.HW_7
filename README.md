Идемпотенстность создания заказа достигнута с помощью версионирования
коллекции заказов каждого пользователя. Сервер присылает заголовок ETag
с версией коллекции заказов пользователя. Клиент при изменении коллекции
передает заголовок If-Match с версией, которую он знает. Сервер проверяет,
если If-Match совпадает с версией на сервере, то запрос проходит. Если нет,
то отвечает ошибкой 409.

## Инструкция по утсановке и тестированию

1. kubectl create namespace hw

2. kubectl config set-context --current --namespace=hw

3. helm install billing ./billing\ service/billing-chart --atomic

4. helm install notification ./notification\ service/notification-chart --atomic

5. sed -i "s#BILLING_SERVICE_URL#http://billing-billing-chart.hw.svc.cluster.local:9000#" ./order\ service/order-chart/values.yaml

6. sed -i "s#NOTIFICATION_SERVICE_URL#http://notification-notification-chart.hw.svc.cluster.local:9000#" ./order\ service/order-chart/values.yaml

7. helm install order ./order\ service/order-chart --atomic

8. newman run ./tests/Otus.SoftwareArchitect.HW7.postman_collection.json
