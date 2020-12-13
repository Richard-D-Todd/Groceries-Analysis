select x.delivery_date, x.total, count_ordered, count_subs, count_unavailable
from(
	select i.delivery_date, i.total, count_subs, count_ordered
	from(
		select od.delivery_date, od.total, count(di.substitution) as count_ordered
		from order_Details od
		inner join delivered_items di
		on od.order_number = di.order_number
		where di.substitution = false
		group by od.delivery_date, od.total
		order by od.delivery_date asc
	) as i
	left join
	(
		select od.delivery_date, od.total, count(di.substitution) as count_subs
		from order_details od
		inner join delivered_items di
		on od.order_number = di.order_number
		where di.substitution = true
		group by od.delivery_date, od.total
		order by od.delivery_date asc
	) as j on i.delivery_date = j.delivery_date
) as x
left join
(
select od.delivery_date, od.total, count(ui.id) as count_unavailable
from order_details od
inner join unavailable_items ui
on od.order_number = ui.order_number
group by od.delivery_date, od.total
order by od.delivery_date asc
) as y on x.delivery_date = y.delivery_date;