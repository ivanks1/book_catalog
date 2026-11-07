import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'book_catalog.settings')
django.setup()

from books.models import Author, Book, BookDetail

# Удаляем все старые записи
BookDetail.objects.all().delete()
Book.objects.all().delete()
Author.objects.all().delete()


# Создаём список авторов
authors = [
    Author(id=1, name='Михаил Лермонтов', img_src='', years_of_age='1814-1841',
           bio='Русский поэт и писатель.',
           works='Герой нашего времени, Мцыри'),

    Author(id=2, name='Иван Тургенев', img_src='', years_of_age='1818-1883',
           bio='Русский писатель и драматург.',
           works='Отцы и дети, Муму'),

    Author(id=3, name='Максим Горький', img_src='', years_of_age='1868-1936',
           bio='Русский писатель и драматург.',
           works='На дне, Мать'),

    Author(id=4, name='Жюль Верн', img_src='', years_of_age='1828-1905',
           bio='Французский писатель, основоположник научной фантастики.',
           works='Дети капитана Гранта, Таинственный остров'),

    Author(id=5, name='Марк Твен', img_src='', years_of_age='1835-1910',
           bio='Американский писатель и юморист.',
           works='Приключения Тома Сойера, Гекльберри Финн'),

    Author(id=6, name='Оскар Уайльд', img_src='', years_of_age='1854-1900',
           bio='Ирландский писатель и поэт.',
           works='Портрет Дориана Грея, Счастливый принц'),

    Author(id=7, name='Антуан де Сент-Экзюпери', img_src='', years_of_age='1900-1944',
           bio='Французский писатель и лётчик.',
           works='Маленький принц, Ночной полёт'),

    Author(id=8, name='Рэй Брэдбери', img_src='', years_of_age='1920-2012',
           bio='Американский писатель-фантаст.',
           works='451 градус по Фаренгейту, Марсианские хроники'),

    Author(id=9, name='Артур Конан Дойл', img_src='', years_of_age='1859-1930',
           bio='Английский писатель и врач.',
           works='Шерлок Холмс, Затерянный мир'),

    Author(id=10, name='Габриэль Гарсиа Маркес', img_src='', years_of_age='1927-2014',
           bio='Колумбийский писатель и журналист.',
           works='Сто лет одиночества, Любовь во время чумы'),

    Author(id=11, name='Джек Лондон', img_src='', years_of_age='1876-1916',
           bio='Американский писатель и журналист.',
           works='Белый Клык, Зов предков'),

    Author(id=12, name='Пауло Коэльо', img_src='', years_of_age='1947-',
           bio='Бразильский писатель.',
           works='Алхимик, Вероника решает умереть'),

    Author(id=13, name='Льюис Кэрролл', img_src='', years_of_age='1832-1898',
           bio='Английский писатель и математик.',
           works='Алиса в Стране чудес, Алиса в Зазеркалье'),

    Author(id=14, name='Виктор Гюго', img_src='', years_of_age='1802-1885',
           bio='Французский писатель и поэт.',
           works='Отверженные, Собор Парижской Богоматери'),

    Author(id=15, name='Джон Толкин', img_src='', years_of_age='1892-1973',
           bio='Английский писатель и филолог.',
           works='Властелин колец, Хоббит')
]

# Массово добавляем авторов в базу данных
Author.objects.bulk_create(authors)

# Создаём список книг
books = [
    Book(id=1, title='Герой нашего времени', author_id=1,
         img_src='', publication_date='1840-01-01',
         short_desc='Роман о жизни и судьбе Печорина.'),

    Book(id=2, title='Отцы и дети', author_id=2,
         img_src='', publication_date='1862-01-01',
         short_desc='Роман о конфликте поколений и разных взглядах на жизнь.'),

    Book(id=3, title='На дне', author_id=3,
         img_src='', publication_date='1902-01-01',
         short_desc='Пьеса о жизни бедных людей в ночлежке.'),

    Book(id=4, title='Дети капитана Гранта', author_id=4,
         img_src='', publication_date='1868-01-01',
         short_desc='Приключенческая история о поисках пропавшего капитана.'),

    Book(id=5, title='Приключения Тома Сойера', author_id=5,
         img_src='', publication_date='1876-01-01',
         short_desc='История весёлых приключений мальчика Тома.'),

    Book(id=6, title='Портрет Дориана Грея', author_id=6,
         img_src='', publication_date='1890-01-01',
         short_desc='История молодого человека, чей портрет стареет вместо него.'),

    Book(id=7, title='Маленький принц', author_id=7,
         img_src='', publication_date='1943-01-01',
         short_desc='Сказка о путешествии маленького принца и дружбе.'),

    Book(id=8, title='451 градус по Фаренгейту', author_id=8,
         img_src='', publication_date='1953-01-01',
         short_desc='Антиутопия о мире, где запрещено читать книги.'),

    Book(id=9, title='Собака Баскервилей', author_id=9,
         img_src='', publication_date='1902-01-01',
         short_desc='Детективная история о загадочном проклятии семьи.'),

    Book(id=10, title='Сто лет одиночества', author_id=10,
         img_src='', publication_date='1967-01-01',
         short_desc='История нескольких поколений семьи Буэндиа.'),

    Book(id=11, title='Белый Клык', author_id=11,
         img_src='', publication_date='1906-01-01',
         short_desc='История волка, который учится жить среди людей.'),

    Book(id=12, title='Алхимик', author_id=12,
         img_src='', publication_date='1988-01-01',
         short_desc='История пастуха, отправившегося искать своё сокровище.'),

    Book(id=13, title='Алиса в Стране чудес', author_id=13,
         img_src='', publication_date='1865-01-01',
         short_desc='Сказочная история о путешествии Алисы в необычный мир.'),

    Book(id=14, title='Отверженные', author_id=14,
         img_src='', publication_date='1862-01-01',
         short_desc='Роман о справедливости, милосердии и человеческой судьбе.'),

    Book(id=15, title='Хоббит', author_id=15,
         img_src='', publication_date='1937-09-21',
         short_desc='Приключения хоббита Бильбо Бэггинса и его друзей.')
]

# Массово добавляем книги в базу данных
Book.objects.bulk_create(books)

# Создаём список описаний книг
book_details = [
    BookDetail(id=1, book_id=1,
               description='Печорин — молодой офицер, который ищет смысл жизни и сталкивается с разными испытаниями.'),

    BookDetail(id=2, book_id=2,
               description='Произведение рассказывает о противостоянии молодых нигилистов и старшего поколения.'),

    BookDetail(id=3, book_id=3,
               description='Герои произведения живут в бедности и пытаются найти надежду на лучшую жизнь.'),

    BookDetail(id=4, book_id=4,
               description='Группа путешественников отправляется в опасное путешествие, чтобы найти капитана Гранта.'),

    BookDetail(id=5, book_id=5,
               description='Том Сойер переживает множество интересных приключений вместе со своим другом Геком.'),

    BookDetail(id=6, book_id=6,
               description='Дориан Грей хочет сохранить молодость, но его поступки отражаются на его портрете.'),

    BookDetail(id=7, book_id=7,
               description='Маленький принц путешествует по планетам и узнаёт о дружбе, любви и ответственности.'),

    BookDetail(id=8, book_id=8,
               description='Главный герой живёт в обществе, где книги уничтожаются, и начинает сомневаться в системе.'),

    BookDetail(id=9, book_id=9,
               description='Шерлок Холмс расследует загадочную смерть и легенду о страшной собаке.'),

    BookDetail(id=10, book_id=10,
               description='Роман описывает историю семьи Буэндиа на протяжении нескольких поколений.'),

    BookDetail(id=11, book_id=11,
               description='Белый Клык проходит путь от дикого животного до верного друга человека.'),

    BookDetail(id=12, book_id=12,
               description='Молодой пастух отправляется в путешествие, чтобы исполнить свою мечту.'),

    BookDetail(id=13, book_id=13,
               description='Алиса попадает в волшебный мир, где встречает необычных персонажей.'),

    BookDetail(id=14, book_id=14,
               description='Жан Вальжан пытается изменить свою жизнь и стать хорошим человеком.'),

    BookDetail(id=15, book_id=15,
               description='Бильбо отправляется в путешествие с гномами, чтобы вернуть их сокровища.')
]

# Массово добавляем подробности книг в базу данных
BookDetail.objects.bulk_create(book_details)


print('15 авторов, 15 книг и 15 описаний успешно добавлены!')