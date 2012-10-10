==========================================================
 :mod:`boing.core.observer` --- Observables and observers
==========================================================

.. module:: boing.core.observer
   :synopsis: Observables and observers

The module :mod:`boing.core.observer` provides an implementation of
the Observer design pattern.

Rather than the standard behaviour, this implementation enables the
:class:`Observable` objects to trigger only a subset of all the
current registered :class:`Observer` objects.

.. note:: The notification mechanism relies on the SIGNAL-SLOT
   mechanism of the Qt eventloop, thus a QApplication must be running
   in order to ensure that notifications are processed.

.. class:: Observable(parent=None)

   :class:`Observable` objects can be subscribed by a list of
   :class:`Observer` instances. An Observable can trigger all or only
   a subset of the subscribed observers by invoking the method
   :meth:`trigger`. The attribute *parent* defines the parent object
   of the observable.

   .. attribute:: observerAdded

      Signal emitted when a new observer is added.

   .. attribute:: observerRemoved

      Signal emitted when a registered observer is removed.

   .. method:: observers()

      Return an iterator over the subscribed observers.

   .. method:: addObserver(observer, mode=QtCore.Qt.QueuedConnection)

      Subscribe *observer* as a new observer. Return whether
      *observer* has been correctly added.

   .. method:: removeObserver(observer)

      Unsubscribe *observer*. Return whether *observer* has been
      correctly removed.

   .. method:: clear()

      Unsubscribe all registered observers.

   .. method:: notify(*restrictions)

      Trigger all the subscribed observers if *restrictions* is empty,
      otherwise trigger only the registered observers in
      *restrictions*.

   .. note:: The list of the subscribed observers is composed by weak
      references, so it is necessary to keep both observables and
      observers alive.

.. class:: Observer(react=None, hz=None, parent=None)

    :class:`Observer` objects can be subscribed to many
    :class:`Observable` instances in order to listen to their
    notifications. The argument *react* can be set to the handler
    function (it must accept one argument) that will be called as
    consequence of an observable notification. If *react* is None, the
    member method :meth:`_react` will be called. *hz* defines the rate
    at which the observer will react to notifications. Available
    values are:

    * None    --- immediately;
    * 0       --- never;
    * <float> --- at the selected frequency (in hz).

    *parent* defines the observers parent.

    .. attribute:: observableAdded

       Signal emitted when the observer is subscribed to a new
       observable.

    .. attribute:: observableRemoved

       Signal emitted when the observer is unsubscribed from an
       observable.

    .. method:: observed

       Return an iterator over the observables it is subscribed to.

    .. method:: subscribeTo(observable, mode=QtCore.Qt.QueuedConnection)

       Subscribe to *observable*. Return whether *observer* has
       been successfully subscribed to.

    .. method:: unsubscribeFrom(observable)

       Unsubscribe from *observable*. Return whether *observable*
       has been successfully found and removed.

    .. method:: clear()

       Unsubscribe from all observed observables.

    .. method:: hz()

       Return when the observer will react to the
       notifications. Possible values:

       * None    --- immediately;
       * 0       --- never;
       * <float> --- at the selected frequency (in hz).

    .. method:: queue()

       Return an iterator over the observables that have triggered
       without having being reacted to yet.

    .. method:: _react(observable)

       Handler method invoked as a result of the notification of
       *observable*, but only if the :class:`Observer` instance has
       not been created with a custom *react* handler.

    .. note:: The list of the subscribed observables is composed by
       weak references, so it is necessary to keep both observables
       and observers alive.
